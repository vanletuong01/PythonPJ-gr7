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
    st.error("⚠️ Không tìm thấy module AI.")

# ===== CSS STYLING =====
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

# ===== LẤY THÔNG TIN SESSION =====
selected_session = st.session_state.get("selected_session")
class_info = st.session_state.get("selected_class_info", {})

if not selected_session or not class_info:
    st.warning("⚠️ Vui lòng chọn lớp và buổi học trước!")
    if st.button("← Quay lại"): st.switch_page("pages/class_detail.py")
    st.stop()

selected_class_id = class_info.get("ClassID")

# Xử lý ngày (YYYY-MM-DD)
try:
    raw_date = selected_session.get("value") or selected_session.get("date_raw") or selected_session.get("date")
    if isinstance(raw_date, str) and "/" in raw_date:
         SESSION_DATE_STR = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
         SESSION_DATE_STR = str(raw_date)
except:
    SESSION_DATE_STR = datetime.now().strftime("%Y-%m-%d")

today = datetime.now().date()
try:
    session_date = datetime.strptime(SESSION_DATE_STR, "%Y-%m-%d").date()
except:
    session_date = today

if today != session_date:
    st.error("Chỉ được điểm danh trong đúng ngày học!")
    st.stop()

# ===== HÀM DB (PORT 3306) =====
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "python_project"),
        port=3306, # Cố định cổng 3306
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def load_attendance_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lấy danh sách đã điểm danh
        cursor.execute("""
            SELECT s.StudentID, st.FullName, st.StudentCode, c.ClassName, a.Time
            FROM attendance a
            JOIN study s ON a.StudyID = s.StudyID
            JOIN student st ON s.StudentID = st.StudentID
            JOIN class c ON s.ClassID = c.ClassID
            WHERE s.ClassID = %s AND a.Date = %s
            ORDER BY a.Time DESC
        """, (selected_class_id, SESSION_DATE_STR))
        attended = list(cursor.fetchall())
        
        # Lấy danh sách tất cả sinh viên
        cursor.execute("""
            SELECT s.StudyID, st.StudentID, st.FullName, st.StudentCode, c.ClassName
            FROM study s
            JOIN student st ON s.StudentID = st.StudentID
            JOIN class c ON s.ClassID = c.ClassID
            WHERE s.ClassID = %s
        """, (selected_class_id,))
        all_students = list(cursor.fetchall())
        
        conn.close()
        
        for row in attended:
            row["Time"] = str(row["Time"]) if row["Time"] else "Thủ công"
            
        return attended, all_students
    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        return [], []

if not st.session_state.att_loaded:
    att, all_s = load_attendance_data()
    st.session_state.att_students = att
    st.session_state.all_students_cache = all_s
    st.session_state.att_loaded = True

# ===== CALLBACK VIDEO (LOG CHI TIẾT) =====
def create_video_callback(class_id, date_str, queue_ref):
    def video_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        
        try:
            result = match_image_and_check_real(img)
            
            # [DEBUG] Chỉ in khi tìm thấy mặt
            if result and result.get("faces") and len(result["faces"]) > 0:
                print(f"🤖 [AI] Found: {len(result['faces'])} faces")
            
            if result and result.get("faces"):
                for face in result["faces"]:
                    if face.get("found") and face.get("student"):
                        student = face["student"]
                        student_id = student.get("id")
                        name = student.get("name", "Unknown")
                        similarity = face.get("similarity", 0)
                        box = face.get("box")
                        
                        msg = "Error"
                        try:
                            # --- KẾT NỐI DB RIÊNG CHO LUỒNG NÀY ---
                            conn = pymysql.connect(
                                host=os.getenv("DB_HOST", "localhost"),
                                user=os.getenv("DB_USER", "root"),
                                password=os.getenv("DB_PASSWORD", ""),
                                database=os.getenv("DB_NAME", "python_project"),
                                port=3306,
                                charset="utf8mb4"
                            )
                            cursor = conn.cursor()
                            
                            # 1. Tìm StudyID
                            cursor.execute("SELECT StudyID FROM study WHERE StudentID = %s AND ClassID = %s", (student_id, class_id))
                            study_row = cursor.fetchone()
                            
                            if study_row:
                                study_id = study_row[0]
                                # 2. Kiểm tra trùng
                                cursor.execute("SELECT AttendanceID FROM attendance WHERE StudyID = %s AND Date = %s", (study_id, date_str))
                                if cursor.fetchone():
                                    msg = "Duplicate"
                                else:
                                    # 3. INSERT VÀO DB
                                    print(f"📝 [INSERT] {name} - Sim: {similarity}")
                                    cursor.execute("""
                                        INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                                        VALUES (%s, %s, CURTIME(), %s)
                                    """, (study_id, date_str, f"sim:{similarity:.2f}"))
                                    conn.commit() # QUAN TRỌNG
                                    msg = "Success"
                                    print(f"✅ [SAVED] Saved {name} to DB!")
                            else:
                                print(f"❌ [LOGIC] SV ID {student_id} không thuộc Lớp {class_id}")
                                msg = "NotInClass"
                                
                            conn.close()
                        except Exception as db_err:
                            print(f"🔥 [DB ERROR] {db_err}")

                        # Gửi ra UI
                        if msg == "Success":
                            queue_ref.put({
                                "StudentID": student_id,
                                "FullName": name,
                                "StudentCode": student.get("mssv", "Unknown"),
                                "Time": datetime.now().strftime("%H:%M:%S")
                            })

                        # Vẽ khung
                        if box:
                            x1, y1, x2, y2 = map(int, box)
                            if msg == "Success": color = (0, 255, 0)
                            elif msg == "Duplicate": color = (0, 165, 255)
                            elif msg == "NotInClass": color = (0, 0, 255)
                            else: color = (128, 128, 128)
                            
                            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(img, name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        except Exception as e:
            print(f"AI Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    return video_callback

# ===== GIAO DIỆN =====
col_back, col_info = st.columns([0.5, 9.5])
with col_back:
    if st.button("←", help="Quay lại"):
        st.session_state.att_loaded = False
        st.switch_page("pages/select_session.py")

with col_info:
    st.markdown(f"""
    <div class="att-header">
        <h3 style="margin:0;">📸 ĐIỂM DANH: {selected_session.get('label', f"Ngày {SESSION_DATE_STR}")}</h3>
        <p style="margin:0;">Lớp: {class_info.get('ClassName')} - {class_info.get('FullClassName')}</p>
    </div>
    """, unsafe_allow_html=True)

# Thống kê
total_sv = len(st.session_state.all_students_cache)
attended_sv = len(st.session_state.att_students)
absent_sv = total_sv - attended_sv

m1, m2, m3 = st.columns(3)
m1.markdown(f'<div class="metric-box"><div class="metric-value">{total_sv}</div><div class="metric-label">Tổng sĩ số</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#22c55e">{attended_sv}</div><div class="metric-label">Đã điểm danh</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#ef4444">{absent_sv}</div><div class="metric-label">Vắng</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# CAMERA & DANH SÁCH
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

col_cam, col_list = st.columns([1.5, 1])

with col_cam:
    st.info("Hướng mặt vào camera để điểm danh")
    
    callback_func = create_video_callback(selected_class_id, SESSION_DATE_STR, result_queue)
    
    webrtc_streamer(
        key="attendance_cam",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
        video_frame_callback=callback_func,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col_list:
    tab1, tab2 = st.tabs(["✅ Đã điểm danh", "❌ Chưa điểm danh"])
    
    with tab1:
        # Đã sửa lỗi use_container_width
        if st.button("🔄 Làm mới danh sách", key="refresh_btn"): 
            st.session_state.att_loaded = False
            st.rerun()

        if not st.session_state.att_students:
            st.info("Chưa có ai điểm danh.")
        else:
            for s in st.session_state.att_students:
                st.markdown(f"""
                <div class="att-card">
                    <b>{s.get('FullName', 'Unknown')}</b><br>
                    <small>MSSV: {s.get('StudentCode')} | ⏰ {s.get('Time')}</small>
                </div>
                """, unsafe_allow_html=True)
                
    with tab2:
        attended_ids = [s['StudentID'] for s in st.session_state.att_students]
        absent_list = [s for s in st.session_state.all_students_cache if s['StudentID'] not in attended_ids]
        
        if not absent_list:
            st.success("Lớp đã đi học đủ!")
        else:
            for s in absent_list:
                st.markdown(f"""
                <div class="absent-card">
                    <b>{s['FullName']}</b><br>
                    <small>MSSV: {s['StudentCode']}</small>
                </div>
                """, unsafe_allow_html=True)

if not result_queue.empty():
    new_data_found = False
    while not result_queue.empty():
        new_student = result_queue.get()
        is_exist = any(s['StudentID'] == new_student['StudentID'] for s in st.session_state.att_students)
        if not is_exist:
            st.session_state.att_students.insert(0, new_student)
            new_data_found = True
            st.toast(f"✅ Đã điểm danh: {new_student['FullName']}")
    
    if new_data_found:
        st.rerun()