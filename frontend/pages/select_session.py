import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import sys

# ===== CẤU HÌNH =====
st.set_page_config(
    page_title="Chọn buổi điểm danh",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== IMPORT =====
sys.path.append(str(Path(__file__).parent.parent))
from services.api_client import get_attendance_by_date, get_session_detail

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "attendance.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== KIỂM TRA ĐĂNG NHẬP VÀ LỚP HỌC =====
if not st.session_state.get("logged_in"):
    st.warning("Vui lòng đăng nhập!")
    st.stop()

class_info = st.session_state.get("selected_class_info", {})
if not class_info:
    st.warning("Vui lòng chọn lớp học trước!")
    st.stop()

# ===== HEADER =====
col_back, col_title = st.columns([0.5, 9.5])
with col_back:
    if st.button("←", key="btn_back", help="Quay lại Dashboard"):
        st.switch_page("pages/dashboard.py")

with col_title:
    st.markdown('<h3 style="margin:0; color:#0a2540;">ĐIỂM DANH LỚP</h3>', unsafe_allow_html=True)

# ===== THÔNG TIN LỚP (3 TEXTBOX) =====
c1, c2, c3 = st.columns(3)
with c1:
    st.text_input("Lớp:", value=class_info.get("ClassName", ""), disabled=True, label_visibility="visible")
with c2:
    st.text_input("Môn:", value=class_info.get("FullClassName", ""), disabled=True, label_visibility="visible")
with c3:
    st.text_input("Mã môn học:", value=class_info.get("CourseCode", ""), disabled=True, label_visibility="visible")

st.markdown("<br>", unsafe_allow_html=True)

# ===== TẠO DANH SÁCH BUỔI HỌC TỰ ĐỘNG =====
try:
    date_start_str = str(class_info.get("DateStart", "2025-04-20"))
    date_end_str = str(class_info.get("DateEnd", "2025-06-30"))
    
    start_date = datetime.strptime(date_start_str, "%Y-%m-%d")
    end_date = datetime.strptime(date_end_str, "%Y-%m-%d")
    
    sessions = []
    session_number = 1
    current_date = start_date
    
    # CHỈ TẠO 12 BUỔI, mỗi buổi cách nhau 1 tuần
    while session_number <= 12 and current_date <= end_date:
        sessions.append({
            "session_number": session_number,
            "date": current_date.strftime("%d/%m/%Y"),
            "date_raw": current_date,
            "attended": 0,
            "absent": 0
        })
        current_date += timedelta(weeks=1)
        session_number += 1

except Exception as e:
    st.error(f"Lỗi tính toán ngày học: {e}")
    sessions = []

# ===== DROPDOWN CHỌN BUỔI HỌC =====
st.markdown('<h4 style="color:#333; margin-bottom:10px;">Chọn buổi điểm danh</h4>', unsafe_allow_html=True)

if len(sessions) > 0:
    # Tạo dictionary để mapping index -> session
    session_options = {
        f"Buổi {s['session_number']} - {s['date']}": s 
        for s in sessions
    }
    
    # Lấy giá trị đã chọn trước đó (nếu có)
    current_selected = st.session_state.get("selected_session")
    default_index = 0
    
    if current_selected:
        # Tìm index của buổi đã chọn
        for idx, (label, sess) in enumerate(session_options.items()):
            if sess['session_number'] == current_selected['session_number']:
                default_index = idx
                break
    
    # Dropdown
    selected_label = st.selectbox(
        "Chọn buổi học:",
        options=list(session_options.keys()),
        index=default_index,
        key="session_dropdown"
    )
    
    # Lưu buổi đã chọn vào session_state
    st.session_state["selected_session"] = session_options[selected_label]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hiển thị thông tin buổi đã chọn
    selected = st.session_state["selected_session"]
    st.info(f"📌 Đã chọn: **Buổi {selected['session_number']}** - {selected['date']}")
    
    # ===== NÚT MỞ CAMERA (ĐÃ ENABLED) =====
    if st.button("📷 MỞ CAMERA ĐIỂM DANH", use_container_width=True, type="primary"):
        st.switch_page("pages/attendance.py")
    
else:
    st.warning("⚠️ Không có buổi học nào để chọn. Vui lòng kiểm tra lại ngày bắt đầu/kết thúc của lớp.")

st.markdown("<br>", unsafe_allow_html=True)

# ===== HIỂN THỊ DANH SÁCH BUỔI HỌC (BẢNG THAM KHẢO) =====
st.markdown('<h4 style="color:#333; margin-top:30px;">Danh sách các buổi học</h4>', unsafe_allow_html=True)
st.markdown('<div class="session-list">', unsafe_allow_html=True)

for session in sessions:
    col_session, col_date, col_status, col_action = st.columns([1, 2, 3, 1.5])

    # Lấy số sinh viên đã và chưa điểm danh cho buổi này
    class_id = class_info.get("ClassID")
    session_date_api = session['date_raw'].strftime("%Y-%m-%d")
    data = get_session_detail(class_id, session_date_api)
    if data and data.get("success"):
        total_attended = data.get("total_attended", 0)
        total_absent = data.get("total_absent", 0)
    else:
        total_attended = "__"
        total_absent = "__"

    with col_session:
        st.markdown(f"<div style='padding:10px; font-weight:600;'>Buổi {session['session_number']}</div>", unsafe_allow_html=True)

    with col_date:
        st.markdown(f"<div style='padding:10px;'>{session['date']}</div>", unsafe_allow_html=True)

    with col_status:
        st.markdown(f"""
        <div style='padding:10px; font-size:14px; color:#666;'>
            Đã điểm danh: <b>{total_attended}</b> &nbsp;&nbsp; Chưa điểm danh: <b>{total_absent}</b>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        if st.button(f"Chi tiết", key=f"detail_{session['session_number']}", use_container_width=True):
            st.session_state["selected_session"] = session
            st.switch_page("pages/session_detail.py")

st.markdown('</div>', unsafe_allow_html=True)