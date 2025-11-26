import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import cv2
import av
import threading
import pymysql
import os
import queue
import time  # <--- Thêm thư viện time để xử lý delay

# --- LOAD BIẾN MÔI TRƯỜNG ---
from dotenv import load_dotenv
load_dotenv()
# ----------------------------

# ===== CẤU HÌNH TRANG =====
st.set_page_config(page_title="Điểm danh Camera", layout="wide", initial_sidebar_state="collapsed")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import AI
try:
    from backend.app.ai.smart_face_attendance import match_image_and_check_real
except ImportError:
    def match_image_and_check_real(img): return None

# ===== CẤU HÌNH STUN SERVER (QUAN TRỌNG ĐỂ CHẠY ONLINE) =====
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ===== CSS STYLING (GIỮ NGUYÊN CỦA BẠN) =====
st.markdown("""
    <style>
        .att-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px; }
        .att-card { background: #f0fdf4; border-left: 5px solid #22c55e; padding: 12px; margin-bottom: 8px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .absent-card { background: #fef2f2; border-left: 5px solid #ef4444; padding: 12px; margin-bottom: 8px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }
        .metric-value { font-size: 32px; font-weight: bold; color: #1e40af; }
        .metric-label { font-size: 14px; color: #64748b; margin-top: 5px; }
        div[data-testid="stToast"] { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; border: 1px solid #c3e6cb; }
    </style>
""", unsafe_allow_html=True)

# ===== QUEUE TOÀN CỤC =====
@st.cache_resource
def get_result_queue():
    return queue.Queue()

result_queue = get_result_queue()

# Session State
if "att_students" not in st.session_state: st.session_state.att_students = []
if "all_students_cache" not in st.session_state: st.session_state.all_students_cache = []
if "att_loaded" not in st.session_state: st.session_state.att_loaded = False

# ===== LẤY THÔNG TIN SESSION TỪ TRANG TRƯỚC =====
selected_session = st.session_state.get("selected_session")
class_info = st.session_state.get("selected_class_info", {})

if not selected_session or not class_info:
    st.warning("⚠️ Vui lòng chọn lớp và buổi học trước!")
    if st.button("← Quay lại"): st.switch_page("pages/class_detail.py")
    st.stop()

selected_class_id = class_info.get("ClassID")

# Xử lý ngày học
try:
    if isinstance(selected_session.get("date_raw"), datetime):
        SESSION_DATE_STR = selected_session["date_raw"].strftime("%Y-%m-%d")
    else:
        raw_date = selected_session.get("value") or selected_session.get("date")
        if isinstance(raw_date, str) and "/" in raw_date:
             SESSION_DATE_STR = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        else:
             SESSION_DATE_STR = str(raw_date)
except:
    SESSION_DATE_STR = datetime.now().strftime("%Y-%m-%d")

# Kiểm tra ngày hiện tại
today = datetime.now().date()
try:
    session_date = datetime.strptime(SESSION_DATE_STR, "%Y-%m-%d").date()
except:
    session_date = today

if today != session_date:
    st.error(f"❌ Bạn không thể điểm danh hôm nay ({today}). Buổi học này diễn ra vào ngày {session_date}.")
    if st.button("Quay lại"): st.switch_page("pages/select_session.py")
    st.stop()

# ===== HÀM KẾT NỐI DATABASE =====
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "python_project"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def load_attendance_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.StudentID, st.FullName, st.StudentCode, a.Time
            FROM attendance a
            JOIN study s ON a.StudyID = s.StudyID
            JOIN student st ON s.StudentID = st.StudentID
            WHERE s.ClassID = %s AND a.Date = %s
            ORDER BY a.Time DESC
        """, (selected_class_id, SESSION_DATE_STR))
        attended = list(cursor.fetchall())
        
        cursor.execute("""
            SELECT s.StudyID, st.StudentID, st.FullName, st.StudentCode
            FROM study s
            JOIN student st ON s.StudentID = st.StudentID
            WHERE s.ClassID = %s
        """, (selected_class_id,))
        all_students = list(cursor.fetchall())
        
        conn.close()
        for row in attended:
            row["Time"] = str(row["Time"]) if row["Time"] else "Thủ công"
        return attended, all_students
    except Exception as e:
        st.error(f"❌ Lỗi kết nối CSDL: {e}")
        return [], []

if not st.session_state.att_loaded:
    att, all_s = load_attendance_data()
    st.session_state.att_students = att
    st.session_state.all_students_cache = all_s
    st.session_state.att_loaded = True

# ===== CALLBACK VIDEO (ĐÃ ĐƯỢC TỐI ƯU HÓA) =====
def create_video_callback(class_id, date_str, queue_ref):
    # Cache để nhớ sinh viên nào vừa xử lý, tránh spam DB
    processed_cache = {}
    
    def video_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        
        try:
            # Gọi AI nhận diện
            result = match_image_and_check_real(img)
            
            if result and result.get("faces"):
                for face in result["faces"]:
                    if face.get("found") and face.get("student"):
                        student = face["student"]
                        student_id = student.get("id")
                        name = student.get("name", "Unknown")
                        similarity = face.get("similarity", 0)
                        box = face.get("box")
                        
                        # --- LOGIC TỐI ƯU: Chỉ kết nối DB sau mỗi 3 giây ---
                        current_time = time.time()
                        last_processed = processed_cache.get(student_id, 0)
                        
                        msg = ""
                        color = (0, 255, 0) # Màu mặc định xanh lá

                        if current_time - last_processed > 3.0:
                            # Đã qua 3 giây, cho phép xử lý DB
                            try:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                
                                # Tìm StudyID
                                cursor.execute("SELECT StudyID FROM study WHERE StudentID = %s AND ClassID = %s", (student_id, class_id))
                                study_row = cursor.fetchone()
                                
                                if study_row:
                                    study_id = study_row['StudyID']
                                    # Check đã điểm danh chưa
                                    cursor.execute("SELECT AttendanceID FROM attendance WHERE StudyID = %s AND Date = %s", (study_id, date_str))
                                    if cursor.fetchone():
                                        msg = "Duplicate"
                                    else:
                                        # Lưu vào DB
                                        cursor.execute("""
                                            INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                                            VALUES (%s, %s, CURTIME(), %s)
                                        """, (study_id, date_str, f"AI:{similarity:.2f}"))
                                        conn.commit()
                                        msg = "Success"
                                        print(f"✅ Đã lưu điểm danh: {name}")
                                else:
                                    msg = "NotInClass"
                                    
                                conn.close()
                                
                                # Cập nhật cache thời gian
                                processed_cache[student_id] = current_time

                                # Đẩy ra queue nếu thành công
                                if msg == "Success":
                                    queue_ref.put({
                                        "StudentID": student_id,
                                        "FullName": name,
                                        "StudentCode": student.get("mssv", "Unknown"),
                                        "Time": datetime.now().strftime("%H:%M:%S")
                                    })
                                
                            except Exception as db_err:
                                print(f"🔥 [DB ERROR] {db_err}")
                        
                        # Set màu sắc và nhãn hiển thị
                        label_suffix = ""
                        if msg == "Duplicate" or (current_time - last_processed <= 3.0 and processed_cache.get(student_id)):
                             color = (0, 165, 255) # Cam (Đã xong)
                             label_suffix = " (Da DD)"
                        elif msg == "NotInClass":
                             color = (0, 0, 255) # Đỏ
                             label_suffix = " (Sai Lop)"

                        # Vẽ khung
                        if box:
                            x1, y1, x2, y2 = map(int, box)
                            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(img, f"{name}{label_suffix}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        except Exception as e:
            print(f"AI Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    return video_callback

# ===== GIAO DIỆN CHÍNH (FRONTEND) =====
col_back, col_info = st.columns([0.5, 9.5])
with col_back:
    if st.button("←", help="Quay lại danh sách buổi"):
        st.session_state.att_loaded = False
        st.switch_page("pages/select_session.py")

with col_info:
    session_label = selected_session.get('label') or f"Ngày {SESSION_DATE_STR}"
    if 'session_number' in selected_session:
        session_label = f"Buổi {selected_session['session_number']} - {selected_session['date']}"
        
    st.markdown(f"""
    <div class="att-header">
        <h3 style="margin:0;">📸 CAMERA ĐIỂM DANH: {session_label}</h3>
        <p style="margin:0; opacity: 0.9;">Lớp: {class_info.get('ClassName')} - {class_info.get('FullClassName')}</p>
    </div>
    """, unsafe_allow_html=True)

# THỐNG KÊ NHANH
total_sv = len(st.session_state.all_students_cache)
attended_sv = len(st.session_state.att_students)
absent_sv = total_sv - attended_sv

m1, m2, m3 = st.columns(3)
m1.markdown(f'<div class="metric-box"><div class="metric-value">{total_sv}</div><div class="metric-label">Tổng sĩ số</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#22c55e">{attended_sv}</div><div class="metric-label">Đã điểm danh</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#ef4444">{absent_sv}</div><div class="metric-label">Vắng</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# PHẦN CAMERA VÀ DANH SÁCH
col_cam, col_list = st.columns([1.5, 1])

with col_cam:
    st.info("💡 Hướng dẫn: Giữ mặt trong khung hình khoảng 2-3 giây để hệ thống nhận diện.")
    
    # Tạo callback với biến Queue
    callback_func = create_video_callback(selected_class_id, SESSION_DATE_STR, result_queue)
    
    # WebRTC Streamer với cấu hình STUN
    webrtc_streamer(
        key="attendance_cam",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION, # <--- Fix Cloudflare
        video_frame_callback=callback_func,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col_list:
    tab1, tab2 = st.tabs(["✅ Đã điểm danh", "❌ Chưa điểm danh"])
    
    with tab1:
        c_refresh, _ = st.columns([1, 2])
        with c_refresh:
            if st.button("🔄 Cập nhật", key="refresh_btn", use_container_width=True): 
                st.session_state.att_loaded = False
                st.rerun()

        if not st.session_state.att_students:
            st.markdown('<div style="text-align:center; color:#888; padding:20px;">Chưa có sinh viên nào điểm danh</div>', unsafe_allow_html=True)
        else:
            for s in st.session_state.att_students:
                st.markdown(f"""
                <div class="att-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <b>{s.get('FullName', 'Unknown')}</b><br>
                            <small style="color:#555;">MSSV: {s.get('StudentCode')}</small>
                        </div>
                        <div style="text-align:right;">
                            <span style="background:#dcfce7; color:#166534; padding:2px 8px; border-radius:10px; font-size:12px;">Đã có mặt</span><br>
                            <small style="color:#888;">{s.get('Time')}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
    with tab2:
        attended_ids = [s['StudentID'] for s in st.session_state.att_students]
        absent_list = [s for s in st.session_state.all_students_cache if s['StudentID'] not in attended_ids]
        
        if not absent_list:
            st.success("🎉 Tuyệt vời! Lớp đã đi học đầy đủ.")
        else:
            st.write(f"Còn vắng: **{len(absent_list)}** sinh viên")
            for s in absent_list:
                st.markdown(f"""
                <div class="absent-card">
                    <b>{s['FullName']}</b><br>
                    <small>MSSV: {s['StudentCode']}</small>
                </div>
                """, unsafe_allow_html=True)

# ===== XỬ LÝ QUEUE (Cập nhật UI Realtime) =====
if not result_queue.empty():
    new_data_found = False
    while not result_queue.empty():
        new_student = result_queue.get()
        # Check duplicate visual
        is_exist = any(s['StudentID'] == new_student['StudentID'] for s in st.session_state.att_students)
        if not is_exist:
            st.session_state.att_students.insert(0, new_student)
            new_data_found = True
            st.toast(f"✅ Đã điểm danh: {new_student['FullName']}", icon="🎉")
    
    if new_data_found:
        time.sleep(0.5)
        st.rerun()