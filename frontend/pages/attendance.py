import streamlit as st
from pathlib import Path
from datetime import datetime
import requests
import sys

# Import header component
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.header import render_header

st.set_page_config(page_title="Điểm Danh Lớp Học", page_icon="✅", layout="wide")

# Load CSS (chỉ giữ phần form/camera/danh sách, xóa phần header)
css_path = Path(__file__).parent.parent / "public" / "css" / "attendance.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Render header chung
render_header()

# Title
st.markdown('<h1 class="main-title">ĐIỂM DANH LỚP HỌC</h1>', unsafe_allow_html=True)

# Layout 2 cột: camera bên trái, danh sách bên phải
col_left, col_right = st.columns([3, 2], gap="large")

# State
st.session_state.setdefault("att_students", [])

with col_left:
    # Form Buổi/Ngày + Camera to
    st.markdown("""
    <div class="attendance-form-left">
        <div class="form-row">
            <div class="form-label">Buổi:____</div>
            <div class="form-label">Ngày:____</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Camera lớn
    img = st.camera_input("", key="att_cam", label_visibility="collapsed")
    
    if img is not None:
        st.success("✅ Đã chụp ảnh điểm danh")

with col_right:
    # Thời gian realtime
    st.markdown(f"""
    <div class="current-time">{datetime.now().strftime("%H:%M:%S %a,%d/%m/%Y")}</div>
    """, unsafe_allow_html=True)
    
    # Danh sách sinh viên
    st.markdown('<div class="attendance-list-title">📋 Danh sách điểm danh</div>', unsafe_allow_html=True)
    
    if len(st.session_state.att_students) == 0:
        st.info("Chọn lớp/môn để tải danh sách sinh viên")
    else:
        st.markdown('<div class="attendance-list-box">', unsafe_allow_html=True)
        for i, stu in enumerate(st.session_state.att_students):
            cols = st.columns([1, 4, 3, 2])
            cols[0].write(f"**{i+1}**")
            cols[1].write(stu.get("FullName", "N/A"))
            cols[2].write(stu.get("StudentCode", "N/A"))
            status = cols[3].selectbox("", ["✅ Có", "❌ Vắng", "⏰ Muộn"], key=f"att_{i}", label_visibility="collapsed")
            st.session_state.att_students[i]["Status"] = status
        st.markdown('</div>', unsafe_allow_html=True)

# Nút load mẫu + Lưu điểm danh
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔄 Tải danh sách lớp mẫu", use_container_width=True):
        st.session_state.att_students = [
            {"FullName": "Nguyễn Văn A", "StudentCode": "2021001", "Status": "✅ Có"},
            {"FullName": "Trần Thị B", "StudentCode": "2021002", "Status": "✅ Có"},
            {"FullName": "Lê Văn C", "StudentCode": "2021003", "Status": "❌ Vắng"},
            {"FullName": "Phạm Thị D", "StudentCode": "2021004", "Status": "⏰ Muộn"},
        ]
        st.rerun()

with col_btn2:
    if st.button("✅ Lưu điểm danh", type="primary", use_container_width=True):
        if len(st.session_state.att_students) == 0:
            st.error("Chưa có sinh viên nào trong danh sách")
        else:
            try:
                payload = {
                    "class_code": "K45-DHTT",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "records": st.session_state.att_students
                }
                st.success("✅ Đã lưu điểm danh thành công!")
            except Exception as e:
                st.error(f"Lỗi: {e}")