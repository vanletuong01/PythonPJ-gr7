import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))

# DEBUG: In ra toàn bộ hàm trong api_client
import services.api_client as api
print("👉 FUNCTIONS IN api_client:", dir(api))

from components.sidebar_dashboard import render_dashboard_sidebar
from components.header import render_header
from services.api_client import get_students_in_class, get_attendance_session_detail
import streamlit as st

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Chi tiết buổi học", layout="wide", initial_sidebar_state="expanded")

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "class_detail.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_dashboard_sidebar()

# ===== LẤY THÔNG TIN LỚP VÀ BUỔI HỌC =====
class_info = st.session_state.get("selected_class_info", {})
session_number = st.session_state.get("selected_session_number", 1)  # hoặc lấy từ URL params

if not class_info:
    st.warning("Vui lòng chọn lớp học trước.")
    st.stop()

# ===== HEADER =====
render_header(
    class_name=class_info.get("ClassName", ""),
    full_class_name=class_info.get("FullClassName", ""),
    course_code=class_info.get("CourseCode", ""),
    class_id=class_info.get("ClassID", "")
)

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ===== LẤY DỮ LIỆU BUỔI HỌC =====
class_id = class_info.get("ClassID")
students = get_students_in_class(class_id) or []
attendance_detail = get_attendance_session_detail(class_id, session_number) or []

# ===== GIAO DIỆN CHI TIẾT BUỔI HỌC =====
st.markdown("""
<div style='background:#fff;border-radius:12px;padding:24px 32px;max-width:900px;margin:auto;box-shadow:0 2px 8px #eee;'>
    <div style='font-size:22px;font-weight:700;margin-bottom:18px;display:flex;align-items:center;gap:16px;'>
        <span style='cursor:pointer;font-size:20px;'>&larr;</span>
        <span>Chi tiết buổi học</span>
    </div>
""", unsafe_allow_html=True)

# Thông tin buổi học
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.button(f"Buổi {session_number}", disabled=True)
with col2:
    today = datetime.now().strftime("%d/%m/%Y")
    st.button(today, disabled=True)
with col3:
    st.write("")  # Để căn chỉnh

# Thống kê đã/ chưa điểm danh
col4, col5 = st.columns([1, 1])
with col4:
    st.text_input("Đã điểm danh:", value=str(sum(1 for s in attendance_detail if s.get("IsPresent"))), disabled=True)
with col5:
    st.text_input("Chưa điểm danh:", value=str(sum(1 for s in attendance_detail if not s.get("IsPresent"))), disabled=True)

st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)

# ===== DANH SÁCH SINH VIÊN =====
for idx, student in enumerate(students):
    att = next((a for a in attendance_detail if a.get("StudentID") == student.get("StudentID")), {})
    is_present = att.get("IsPresent", False)
    time_str = att.get("Time", "--:--:--") if is_present else "--:--:--"

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        st.text_input("Họ tên:", value=student.get("FullName", ""), key=f"name_{idx}", disabled=True)
    with c2:
        st.text_input("Mssv:", value=student.get("StudentCode", ""), key=f"mssv_{idx}", disabled=True)
    with c3:
        st.selectbox("", options=["Đã điểm danh", "Chưa điểm danh"], index=0 if is_present else 1, key=f"status_{idx}", disabled=True)
    with c4:
        st.button(f"🕒 {time_str}", key=f"time_{idx}", disabled=True)
    with c5:
        st.button("Save", key=f"save_{idx}", disabled=True)

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
