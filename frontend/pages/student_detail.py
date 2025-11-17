import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# ===== IMPORT SIDEBAR VÀ HEADER =====
sys.path.insert(0, str(Path(__file__).parent.parent / "components"))
from sidebar_dashboard import render_dashboard_sidebar
from header import render_header

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "student_detail.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_dashboard_sidebar()

# ===== HEADER =====
render_header()

# ====== DUMMY DATA (thay bằng truy vấn DB thực tế) ======
student = {
    "full_name": "Nguyễn Văn A",
    "student_code": "20123456",
    "class": "CTK42",
    "phone": "0912345678",
    "khoa": "2020",
    "nganh": "CNTT",
    "birth_date": "20/04/2005",
    "cccd": "123456789012"
}

# Giả lập số buổi học của lớp (ví dụ: 4 buổi)
num_sessions = 4
# Giả lập danh sách điểm danh (bạn thay bằng truy vấn DB thực tế)
attendance_list = [
    {"session": 1, "date": "20/04/2025", "status": True, "time": "07:50:00"},
    {"session": 2, "date": "27/04/2025", "status": True, "time": "07:00:00"},
    {"session": 3, "date": "03/05/2025", "status": False, "time": "--:--:--"},
    {"session": 4, "date": "10/05/2025", "status": False, "time": "--:--:--"},
]

# ====== MAIN CONTAINER ======
st.markdown("<div class='student-detail-container'>", unsafe_allow_html=True)
st.markdown("<div class='student-detail-title'>Xem chi tiết sinh viên</div>", unsafe_allow_html=True)

# ====== FORM ======
st.markdown("<form class='student-detail-form'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.text_input("Họ tên:", student["full_name"], key="full_name")
    st.text_input("Lớp:", student["class"], key="class")
    st.text_input("Date:", student["birth_date"], key="birth_date")
with col2:
    st.text_input("Mssv:", student["student_code"], key="student_code")
    st.text_input("SDT:", student["phone"], key="phone")
    st.text_input("CCCD:", student["cccd"], key="cccd")
st.text_input("Khóa:", student["khoa"], key="khoa")
st.text_input("Ngành:", student["nganh"], key="nganh")
st.markdown("</form>", unsafe_allow_html=True)

# ====== BUTTONS ======
st.markdown(
    """
    <div class='btn-row'>
        <button class='btn-save'>SAVE</button>
        <button class='btn-delete'>DELETE</button>
    </div>
    """, unsafe_allow_html=True
)

# ====== TRẠNG THÁI ẢNH & ACTIONS ======
st.markdown(
    """
    <div class='status-row'>
        <span class='status-label'>Trạng thái ảnh:</span>
        <span class='status-yes'>YES</span>
    """, unsafe_allow_html=True
)

# Nút chuyển sang capture_photo.py
if st.button("Lấy ảnh sinh viên", key="capture_photo_btn"):
    st.switch_page("capture_photo.py")

st.markdown(
    """
        <button class='btn-action'>Training data</button>
    </div>
    """, unsafe_allow_html=True
)

# ====== DANH SÁCH ĐIỂM DANH ======
st.markdown("<div class='attendance-list'>", unsafe_allow_html=True)
for i in range(num_sessions):
    att = attendance_list[i] if i < len(attendance_list) else {"session": i+1, "date": "--/--/----", "status": False, "time": "--:--:--"}
    status = "Đã điểm danh" if att["status"] else "Chưa điểm danh"
    status_class = "" if att["status"] else "miss"
    st.markdown(
        f"""
        <div class='attendance-item'>
            <span class='buoi'>Buổi {att['session']}</span>
            <span class='date'>{att['date']}</span>
            <span class='status {status_class}'>{status}</span>
            <span class='time'>{att['time']}</span>
        </div>
        """, unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)