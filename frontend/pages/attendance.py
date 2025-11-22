import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import cv2
import av
import time
import threading
import pymysql
import os
import base64

# ===== CẤU HÌNH =====
st.set_page_config(page_title="Điểm danh", layout="wide", initial_sidebar_state="collapsed")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.ai.smart_face_attendance import match_image_and_check_real

# ===== CSS =====
st.markdown("""
    <style>
        .att-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        }
        .att-card {
            background: #f0fdf4;
            border-left: 5px solid #22c55e;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .absent-card {
            background: #fef2f2;
            border-left: 5px solid #ef4444;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .clock {
            font-size: 24px;
            font-weight: bold;
            color: #fbbf24;
        }
        .metric-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #1e40af;
        }
        .metric-label {
            font-size: 14px;
            color: #64748b;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ===== KIỂM TRA SESSION =====
selected_session = st.session_state.get("selected_session")
if not selected_session:
    st.warning("⚠️ Vui lòng chọn buổi học trước!")
    if st.button("← Quay lại"):
        st.switch_page("pages/select_session.py")
    st.stop()

class_info = st.session_state.get("selected_class_info", {})
selected_class_id = class_info.get("ClassID")

if not selected_class_id:
    st.error("Lỗi: Không tìm thấy ClassID")
    st.stop()

# ===== HÀM LOAD DANH SÁCH ĐÃ ĐIỂM DANH TỪ DB =====
def load_attendance_from_db(class_id, session_date):
    """Load danh sách sinh viên đã điểm danh trong buổi học này"""
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                s.StudentID,
                st.FullName,
                st.StudentCode,
                c.ClassName,
                a.Time,
                a.AttendanceID
            FROM attendance a
            JOIN study s ON a.StudyID = s.StudyID
            JOIN student st ON s.StudentID = st.StudentID
            JOIN class c ON s.ClassID = c.ClassID
            WHERE s.ClassID = %s AND a.Date = %s
            ORDER BY a.Time DESC
        """, (class_id, session_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "StudentID": row["StudentID"],
                "FullName": row["FullName"],
                "StudentCode": row["StudentCode"],
                "ClassName": row["ClassName"],
                "Time": row["Time"].strftime("%H:%M:%S") if row["Time"] else "Thủ công",
                "AttendanceID": row["AttendanceID"]
            })
        
        return result
        
    except Exception as e:
        print(f"❌ Error load_attendance_from_db: {e}")
        return []

# ===== HÀM LẤY DANH SÁCH TẤT CẢ SINH VIÊN =====
def get_all_students_in_class(class_id):
    """Lấy tất cả sinh viên trong lớp"""
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                s.StudyID,
                st.StudentID,
                st.FullName,
                st.StudentCode,
                c.ClassName
            FROM study s
            JOIN student st ON s.StudentID = st.StudentID
            JOIN class c ON s.ClassID = c.ClassID
            WHERE s.ClassID = %s
            ORDER BY st.StudentCode
        """, (class_id,))
        
        rows = cursor.fetchall()
        conn.close()
        return rows
        
    except Exception as e:
        print(f"❌ Error get_all_students_in_class: {e}")
        return []

# ===== KHỞI TẠO STATE =====
if "att_students" not in st.session_state:
    st.session_state.att_students = []
if "checkin_log" not in st.session_state:
    st.session_state.checkin_log = {}
if "att_loaded" not in st.session_state:
    st.session_state.att_loaded = False
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = {"students": []}
if "temp_checkin_log" not in st.session_state:
    st.session_state.temp_checkin_log = {}

# ⭐ LOAD DỮ LIỆU TỪ DB LẦN ĐẦU
if not st.session_state.att_loaded:
    session_date_raw = selected_session.get("date_raw") or selected_session.get("date")
    
    if isinstance(session_date_raw, str):
        try:
            session_date_raw = datetime.strptime(session_date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            pass
    
    loaded_students = load_attendance_from_db(selected_class_id, session_date_raw)
    st.session_state.att_students = loaded_students
    st.session_state.att_loaded = True
    
    print(f"✅ Loaded {len(loaded_students)} students from DB")

# ===== HEADER =====
h_col1, h_col2 = st.columns([0.5, 9.5])

with h_col1:
    if st.button("←", key="btn_back_att"):
        st.session_state.att_loaded = False
        st.session_state["data_refresh_needed"] = True
        st.switch_page("pages/select_session.py")

with h_col2:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="att-header">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="margin:0;">📌 Buổi {selected_session['session_number']} - {selected_session['date']}</h2>
                <p style="margin:5px 0 0 0; opacity:0.9;">
                    {class_info.get('ClassName')} | {class_info.get('FullClassName')}
                </p>
            </div>
            <div class="clock">🕐 {current_time}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== THỐNG KÊ TỔNG QUAN =====
all_students = get_all_students_in_class(selected_class_id)
total_students = len(all_students)
attended_count = len(st.session_state.att_students)
absent_count = total_students - attended_count

col_metric1, col_metric2, col_metric3 = st.columns(3)

with col_metric1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">👥 {total_students}</div>
        <div class="metric-label">Tổng sinh viên</div>
    </div>
    """, unsafe_allow_html=True)

with col_metric2:
    st.markdown(f"""
    <div class="metric-box" style="border-left: 4px solid #22c55e;">
        <div class="metric-value" style="color: #22c55e;">✅ {attended_count}</div>
        <div class="metric-label">Đã điểm danh</div>
    </div>
    """, unsafe_allow_html=True)

with col_metric3:
    st.markdown(f"""
    <div class="metric-box" style="border-left: 4px solid #ef4444;">
        <div class="metric-value" style="color: #ef4444;">❌ {absent_count}</div>
        <div class="metric-label">Vắng</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

lock = threading.Lock()

# ===== HÀM LƯU DB =====
def quick_save_attendance(student_id, class_id, similarity, photo_base64=None):
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT StudyID FROM study WHERE StudentID = %s AND ClassID = %s",
            (student_id, class_id)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "NoStudyID"
        
        study_id = row[0]
        
        cursor.execute(
            "SELECT AttendanceID FROM attendance WHERE StudyID = %s AND Date = CURDATE()",
            (study_id,)
        )
        
        if cursor.fetchone():
            conn.close()
            return "Duplicate"
        
        photo_data = photo_base64 if photo_base64 else f"similarity_{similarity:.2f}"
        
        cursor.execute(
            """
            INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
            VALUES (%s, CURDATE(), CURTIME(), %s)
            """,
            (study_id, photo_data)
        )
        
        conn.commit()
        conn.close()
        return "Success"
        
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return "Error"

# ===== CALLBACK VIDEO =====
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    try:
        result = match_image_and_check_real(img)
        
        if result.get("status") == "ok":
            faces = result.get("faces", [])
            
            for face in faces:
                box = face.get("box")
                if not box:
                    continue
                
                x1, y1, x2, y2 = [int(v) for v in box]
                found = face.get("found")
                student = face.get("student", {})
                name = student.get("name", "Unknown")
                code = student.get("code", "N/A")
                class_name = student.get("class_name", "N/A")
                similarity = face.get("similarity", 0)
                
                if found:
                    color = (0, 255, 0)
                    label = f"{name} ({similarity*100:.0f}%)"
                    
                    with lock:
                        sid = student.get("id")
                        if sid:
                            now = time.time()
                            last = st.session_state.temp_checkin_log.get(sid, 0)
                            
                            if now - last > 5:
                                face_crop = img[y1:y2, x1:x2]
                                _, buffer = cv2.imencode('.jpg', face_crop)
                                photo_b64 = base64.b64encode(buffer).decode()
                                
                                status_db = quick_save_attendance(
                                    sid, 
                                    selected_class_id, 
                                    similarity,
                                    photo_b64
                                )
                                
                                if status_db == "Success":
                                    label += " ✅"
                                    new_student = {
                                        "FullName": name,
                                        "StudentCode": code,
                                        "ClassName": class_name,
                                        "Time": datetime.now().strftime("%H:%M:%S"),
                                        "StudentID": sid
                                    }
                                    st.session_state.temp_attendance["students"].insert(0, new_student)
                                    print(f"✅ Đã thêm: {name}")
                                    
                                elif status_db == "Duplicate":
                                    label += " (Đã có)"
                                    color = (0, 200, 200)
                                
                                st.session_state.temp_checkin_log[sid] = now
                else:
                    color = (0, 165, 255)
                    label = "Unknown"
                
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    except Exception as e:
        print(f"❌ Callback Error: {e}")
    
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# ===== GIAO DIỆN CHÍNH =====
from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode

col_cam, col_list = st.columns([2.5, 1.5])

with col_cam:
    st.markdown("### 📹 Camera điểm danh")
    rtc_config = RTCConfiguration({
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })
    
    webrtc_streamer(
        key="attendance_camera",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_config,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )

with col_list:
    # TAB QUẢN LÝ
    tab1, tab2, tab3 = st.tabs(["✅ Đã điểm danh", "❌ Chưa điểm danh", "🖊️ Điểm danh thủ công"])
    
    # TAB 1: ĐÃ ĐIỂM DANH
    with tab1:
        if st.button("🔄 Cập nhật", width='stretch', type="primary"):
            with lock:
                existing_ids = {s.get("StudentID") for s in st.session_state.att_students}
                for student in st.session_state.temp_attendance["students"]:
                    if student.get("StudentID") not in existing_ids:
                        st.session_state.att_students.insert(0, student)
                        existing_ids.add(student.get("StudentID"))
            st.rerun()
        
        st.write(f"**Tổng: {len(st.session_state.att_students)} sinh viên**")
        
        for s in st.session_state.att_students:
            st.markdown(f"""
            <div class="att-card">
                <div style="font-weight:bold; font-size:16px; color:#065f46;">
                    {s['FullName']}
                </div>
                <div style="margin-top:4px; color:#374151;">
                    📝 MSSV: {s['StudentCode']}<br>
                    🏫 Lớp: {s['ClassName']}<br>
                    ⏰ Thời gian: {s['Time']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 2: CHƯA ĐIỂM DANH
    with tab2:
        attended_ids = {s.get("StudentID") for s in st.session_state.att_students}
        absent_students = [s for s in all_students if s["StudentID"] not in attended_ids]
        
        st.write(f"**Tổng: {len(absent_students)} sinh viên**")
        
        for s in absent_students:
            st.markdown(f"""
            <div class="absent-card">
                <div style="font-weight:bold; font-size:16px; color:#991b1b;">
                    {s['FullName']}
                </div>
                <div style="margin-top:4px; color:#374151;">
                    📝 MSSV: {s['StudentCode']}<br>
                    🏫 Lớp: {s['ClassName']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 3: ĐIỂM DANH THỦ CÔNG
    with tab3:
        attended_ids = {s.get("StudentID") for s in st.session_state.att_students}
        absent_students = [s for s in all_students if s["StudentID"] not in attended_ids]
        
        if absent_students:
            selected_student = st.selectbox(
                "Chọn sinh viên:",
                options=absent_students,
                format_func=lambda x: f"{x['FullName']} - {x['StudentCode']}"
            )
            
            if st.button("✅ Xác nhận điểm danh", width='stretch'):
                try:
                    conn = pymysql.connect(
                        host=os.getenv("DB_HOST", "localhost"),
                        user=os.getenv("DB_USER", "root"),
                        password=os.getenv("DB_PASSWORD", ""),
                        database=os.getenv("DB_NAME", "python_project"),
                        charset="utf8mb4"
                    )
                    cursor = conn.cursor()
                    
                    session_date_raw = selected_session.get("date_raw") or selected_session.get("date")
                    if isinstance(session_date_raw, str):
                        try:
                            session_date_raw = datetime.strptime(session_date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                        except:
                            pass
                    
                    cursor.execute(
                        """
                        INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                        VALUES (%s, %s, NULL, NULL)
                        """,
                        (selected_student["StudyID"], session_date_raw)
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    st.session_state.att_students.insert(0, {
                        "StudentID": selected_student["StudentID"],
                        "FullName": selected_student["FullName"],
                        "StudentCode": selected_student["StudentCode"],
                        "ClassName": selected_student["ClassName"],
                        "Time": "Thủ công"
                    })
                    
                    st.success(f"✅ Đã điểm danh: {selected_student['FullName']}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
        else:
            st.info("✅ Tất cả sinh viên đã điểm danh")

# ⭐ AUTO-REFRESH
import time as time_module
time_module.sleep(2)
with lock:
    if len(st.session_state.temp_attendance["students"]) > 0:
        existing_ids = {s.get("StudentID") for s in st.session_state.att_students}
        for student in st.session_state.temp_attendance["students"]:
            if student.get("StudentID") not in existing_ids:
                st.session_state.att_students.insert(0, student)
                existing_ids.add(student.get("StudentID"))
        st.session_state.temp_attendance["students"] = []
        st.rerun()