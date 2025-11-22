import streamlit as st
from pathlib import Path
import sys
# Import sidebar chuẩn như join_class.py
from components.sidebar_auth import render_auth_sidebar 
from services.api_client import get_majors, get_types, get_shifts, create_class

# ==== PAGE CONFIG ====
st.set_page_config(page_title="Thêm lớp học", layout="wide", initial_sidebar_state="collapsed")

# ==== LOAD CSS ====
add_class_css = Path(__file__).parent.parent / "public" / "css" / "add_class.css"
if add_class_css.exists():
    st.markdown(f"<style>{add_class_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ==== CHECK LOGIN ====
if not st.session_state.get("logged_in", False) or not st.session_state.get("teacher", {}).get("id_login"):
    st.warning("Bạn cần đăng nhập để thực hiện chức năng này.")
    st.switch_page("pages/login.py")
    st.stop()

# ==== RENDER SIDEBAR (Giống join_class.py) ====
render_auth_sidebar()

# ==========================================
# DATA LOADING
# ==========================================
try:
    majors = get_majors() or []
    types = get_types() or []
    shifts = get_shifts() or []
except Exception as e:
    st.error(f"Không kết nối backend: {e}")
    st.stop()

major_dict = {m['MajorID']: m['MajorName'] for m in majors}
type_dict = {t['TypeID']: t['TypeName'] for t in types}
shift_dict = {s['ShiftID']: s['ShiftName'] for s in shifts}

# ==========================================
# HEADER (Nút quay lại + Tiêu đề)
# ==========================================
# Dùng tỷ lệ cột giống join_class.py
col_back, col_title = st.columns([0.15, 6])

with col_back:
    if st.button("←", key="back_home", help="Quay về trang chủ"):
        st.switch_page("app.py")

with col_title:
    # Đã chỉnh margin-bottom nhỏ lại để xóa khoảng trắng thừa
    st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <h1 style='margin:0; font-size: 32px; color: #0a2540; line-height: 1.2;'>THÊM LỚP HỌC</h1>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# FORM NHẬP LIỆU
# ==========================================
# Container cho Form
with st.container():
    col_major, col_type, col_year = st.columns([2,2,1])
    with col_major:
        major_id = st.selectbox("Chọn chuyên ngành", options=list(major_dict.keys()),
                                format_func=lambda x: major_dict.get(x, "N/A"))
    with col_type:
        type_id = st.selectbox("Chọn loại", options=list(type_dict.keys()),
                            format_func=lambda x: type_dict.get(x, "N/A"))
    with col_year:
        year = st.text_input("Năm *", max_chars=4, value="", placeholder="2025")
    
    col_class, col_quantity = st.columns([3,1])
    with col_class:
        course_code = st.text_input("Mã học phần: *", "", placeholder="101")
    with col_quantity:
        quantity = st.number_input("Sĩ số: *", min_value=1, value=30, step=1)
    
    # Tự động tạo mã lớp
    major_code = major_dict.get(major_id, "")
    class_code = f"{year[-2:]}{major_code}{course_code[-2:]}" if (year and major_code and course_code) else ""
    st.text_input("Mã lớp (Tự động):", value=class_code, disabled=True)
    
    teacher = st.text_input("Nhập tên giảng viên: *", value=st.session_state.get("teacher", {}).get("name", ""), placeholder="Nguyễn Văn A")
    semester = st.selectbox("Học kỳ", ["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"])
    
    col_start, col_end, col_weekday = st.columns([2,2,1])
    with col_start:
        date_start = st.date_input("Start: *")
    with col_end:
        date_end = st.date_input("End: *")
    with col_weekday:
        weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        weekday = weekdays[date_start.weekday()]
        st.text_input("Thứ học:", weekday, disabled=True)
    
    shift_id = st.selectbox("Ca học", options=list(shift_dict.keys()),
                            format_func=lambda x: shift_dict.get(x, "N/A"))
    subject = st.text_input("Nhập tên môn học: *", "", placeholder="Toán cao cấp")
    
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    
    if st.button("LƯU LỚP HỌC", use_container_width=True):
        # Validate
        errors = []
        if not year or len(year) != 4: errors.append("Năm phải có 4 chữ số")
        if not course_code: errors.append("Mã học phần thiếu")
        if not teacher.strip(): errors.append("Tên giảng viên thiếu")
        if not subject.strip(): errors.append("Tên môn học thiếu")
        if date_end < date_start: errors.append("Ngày kết thúc phải sau ngày bắt đầu")
        
        if errors:
            for err in errors: st.error(err)
        else:
            payload = {
                "quantity": int(quantity),
                "semester": semester,
                "date_start": str(date_start),
                "date_end": str(date_end),
                "class_name": class_code,                      
                "full_class_name": subject.strip(),             
                "course_code": course_code,               
                "teacher_class": teacher.strip(),
                "session": weekday,                     
                "MajorID": major_id,
                "TypeID": type_id,
                "ShiftID": shift_id,
                "id_login": st.session_state.teacher["id_login"]
            }
            
            with st.spinner("Đang xử lý..."):
                resp = create_class(payload)
            
            if resp.status_code == 200:
                st.success("✅ Tạo lớp thành công!")
                st.balloons()
                if st.button("Về trang chủ"): st.switch_page("app.py")
            else:
                st.error(f"Lỗi: {resp.text}")