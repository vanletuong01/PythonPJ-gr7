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
import importlib
from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode

# ===== CẤU HÌNH =====
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ===== CSS =====
st.markdown("""
    <style>
        .main-title {text-align: center; color: #d90429; font-weight: bold; margin-bottom: 10px;}
        .att-card {
            background-color: #f0fdf4; 
            border-left: 5px solid #22c55e;
            padding: 10px; margin-bottom: 5px; border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ===== LẤY THÔNG TIN LỚP TỪ DASHBOARD =====
from services.api_client import get_classes
classes = get_classes() or []
selected_class_id = st.session_state.get("selected_class_id")
class_info = {}

if selected_class_id:
    found_class = next((c for c in classes if str(c.get("ClassID")) == str(selected_class_id)), None)
    if found_class:
        class_info = found_class

# ===== HEADER MỚI =====
h_col1, h_col2 = st.columns([0.5, 9.5])
with h_col1:
    if st.button("←", key="btn_back_att", help="Quay lại Dashboard"):
        st.session_state["data_refresh_needed"] = True
        st.switch_page("pages/dashboard.py")
with h_col2:
    st.markdown('<h3 class="page-header-title">ĐIỂM DANH LỚP</h3>', unsafe_allow_html=True)

c_info1, c_info2, c_info3 = st.columns(3)
with c_info1:
    st.text_input("Lớp:", value=class_info.get("ClassName", ""), disabled=True)
with c_info2:
    st.text_input("Môn:", value=class_info.get("FullClassName", "") or class_info.get("SubjectName", ""), disabled=True)
with c_info3:
    st.text_input("Mã môn học:", value=class_info.get("CourseCode", ""), disabled=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

selected_class_id = st.session_state.get("selected_class_id")
if not selected_class_id:
    st.warning("⚠️ Vui lòng chọn lớp trước!")
    st.stop()

# ===== HÀM LƯU DB (CHẶN ĐIỂM DANH 2 LẦN) =====
def quick_save_attendance(student_id, class_id, similarity):
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        
        # 1. Tìm StudyID
        sql_find = "SELECT StudyID FROM study WHERE StudentID = %s AND ClassID = %s"
        cursor.execute(sql_find, (student_id, class_id))
        row = cursor.fetchone()
        
        if row:
            study_id = row[0]
            
            # 2. KIỂM TRA TRÙNG LẶP (QUAN TRỌNG)
            # Chỉ cho phép 1 lần điểm danh trong ngày cho môn học này
            sql_check = "SELECT AttendanceID FROM attendance WHERE StudyID = %s AND Date = CURDATE()"
            cursor.execute(sql_check, (study_id,))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return "Duplicate" # Đã điểm danh rồi

            # 3. Insert nếu chưa có
            sql_insert = """
                INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                VALUES (%s, CURDATE(), CURTIME(), %s)
            """
            cursor.execute(sql_insert, (study_id, str(similarity)))
            conn.commit()
            conn.close()
            return "Success"
        else:
            conn.close()
            return "NoStudyID"
            
    except Exception as e:
        print(f"DB Error: {e}")
        return "Error"

# ===== STATE =====
if "att_students" not in st.session_state:
    st.session_state.att_students = []
if "checkin_log" not in st.session_state:
    st.session_state.checkin_log = {}

lock = threading.Lock()

# ===== CALLBACK VIDEO =====
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    # Gọi AI (Code mới trả về danh sách 'faces')
    try:
        result = match_image_and_check_real(img)
        
        if result.get("status") == "ok":
            faces = result.get("faces", [])
            
            # DUYỆT QUA TỪNG MẶT
            for face in faces:
                box = face.get("box")
                if box:
                    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    
                    found = face.get("found")
                    student = face.get("student", {})
                    name = student.get("name", "Unknown")
                    similarity = face.get("similarity", 0)

                    if found:
                        color = (0, 255, 0) # Xanh
                        label = f"{name}"
                        
                        # --- LOGIC LƯU DB ---
                        with lock:
                            sid = student.get("id")
                            if sid:
                                # Kiểm tra thời gian spam (vẫn cần để tránh gọi DB liên tục mỗi giây)
                                now = time.time()
                                try:
                                    last = st.session_state.checkin_log.get(sid, 0)
                                except:
                                    last = 0
                                
                                # Nếu đã qua 5 giây (để check lại DB xem đã lưu chưa)
                                if now - last > 5:
                                    status_db = quick_save_attendance(sid, selected_class_id, similarity)
                                    
                                    if status_db == "Success":
                                        label += " (SAVED!)"
                                        # Cập nhật UI
                                        try:
                                            st.session_state.att_students.insert(0, {
                                                "FullName": name,
                                                "StudentCode": student.get("code"),
                                                "Time": datetime.now().strftime("%H:%M:%S"),
                                                "Status": "✅ Mới"
                                            })
                                        except: pass
                                    elif status_db == "Duplicate":
                                        label += " (DA CO)" # Đã có trong ngày
                                        color = (0, 200, 200) # Màu xanh lơ báo hiệu đã rồi
                                    
                                    # Cập nhật thời gian log để không check DB liên tục
                                    try:
                                        st.session_state.checkin_log[sid] = now
                                    except: pass
                    else:
                        color = (0, 165, 255) # Cam
                        label = "Unknown"

                    # Vẽ khung
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    except Exception as e:
        print(f"Error: {e}")
        
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# ===== UI =====
st.markdown(f'<h1 class="main-title">LỚP: {selected_class_id}</h1>', unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])

with c1:
    rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
    webrtc_streamer(
        key="multi-face-att",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_configuration,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with c2:
    if st.button("🔄 Cập nhật danh sách", use_container_width=True, type="primary"):
        st.rerun()
    
    st.write(f"**Sĩ số điểm danh: {len(st.session_state.att_students)}**")
    for s in st.session_state.att_students:
        st.markdown(f"""
        <div class="att-card">
            <b>{s['FullName']}</b> <br> {s['StudentCode']} - {s['Time']}
        </div>
        """, unsafe_allow_html=True)