from requests import session
import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from components.sidebar_auth import render_auth_sidebar
from services.api_client import get_majors, get_types, get_shifts, create_class

st.set_page_config(page_title="THÊM LỚP HỌC", layout="wide")

# Load CSS
add_class_css = Path(__file__).parent.parent / "public" / "css" / "add_class.css"
if add_class_css.exists():
    st.markdown(f"<style>{add_class_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Render sidebar
render_auth_sidebar()

# Load data
try:
    majors = get_majors() or []
    types = get_types() or []
    shifts = get_shifts() or []
except Exception as e:
    st.error(f"Không kết nối backend: {e}")
    st.stop()

if not majors or not types or not shifts:
    st.warning("Dữ liệu chuyên ngành/loại/ca học trống!")
major_dict = {m['MajorID']: m['MajorName'] for m in majors}
type_dict = {t['TypeID']: t['TypeName'] for t in types}
shift_dict = {s['ShiftID']: s['ShiftName'] for s in shifts}

col_left, col_right = st.columns([1.2, 2])

with col_left:
    avatar_path = Path(__file__).parent.parent / "public" / "images" / "avatar.png"
    if avatar_path.exists():
        st.image(str(avatar_path), width=60)
    
    teacher_name = st.session_state.get("teacher", {}).get("name", "Giáo viên")
    st.markdown(f"<div style='font-weight:600;font-size:18px;margin-top:10px'>{teacher_name}</div>", unsafe_allow_html=True)
    
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=180)
    
    st.markdown("""
        <div style='font-size:22px;font-weight:700;margin-top:10px'>VIETNAM AVIATION ACADEMY</div>
        <div style='font-size:18px;font-weight:500;margin-bottom:20px'>Học Viện Hàng Không Việt Nam</div>
    """, unsafe_allow_html=True)

with col_right:
    # Header với nút quay lại (styled)
    st.markdown("""
    <style>
    div[data-testid="stButton"][key="back_home"] button {
        background: transparent;
        border: none;
        font-size: 28px;
        cursor: pointer;
        padding: 0;
        color: #333;
    }
    div[data-testid="stButton"][key="back_home"] button:hover {
        color: #0066cc;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_back, col_title = st.columns([0.5, 9.5])
    with col_back:
        if st.button("←", key="back_home", help="Quay về trang chủ"):
            st.switch_page("app.py")
    with col_title:
        st.markdown("<h2 style='margin:0'>THÊM LỚP HỌC</h2>", unsafe_allow_html=True)
    
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
    
    major_code = major_dict.get(major_id, "")
    class_code = f"{year[-2:]}{major_code}{course_code[-2:]}" if (year and major_code and course_code) else ""
    st.text_input("Mã lớp:", value=class_code, disabled=True)
    
    teacher = st.text_input("Nhập tên giảng viên: *", "", placeholder="Nguyễn Văn A")
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
    
    st.markdown("<small style='color:#999'>(*) Bắt buộc</small>", unsafe_allow_html=True)
    
    if st.button("SAVE", use_container_width=True):
        # Validate các trường bắt buộc
        errors = []
        if not year or len(year) != 4:
            errors.append("Năm phải có 4 chữ số")
        if not course_code:
            errors.append("Mã học phần không được để trống")
        if not teacher or teacher.strip() == "":
            errors.append("Tên giảng viên không được để trống")
        if not subject or subject.strip() == "":
            errors.append("Tên môn học không được để trống")
        if date_end < date_start:
            errors.append("Ngày kết thúc phải sau ngày bắt đầu")
        
        if errors:
            for err in errors:
                st.error(err)
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
            
            with st.spinner("Đang lưu..."):
                resp = create_class(payload)
            
            if resp.status_code == 200:
                class_info = resp.json()
                st.success("Thêm lớp học thành công!")
                st.balloons()
                
                # Hiển thị thông tin lớp vừa tạo
                st.info(f"""
                **Thông tin lớp học vừa thêm:**
                - **Mã lớp:** {class_info.get('ClassName')}
                - **Tên đầy đủ:** {class_info.get('FullClassName')}
                - **Giảng viên:** {class_info.get('Teacher_class')}
                - **Môn học:** {class_info.get('Session')}
                - **Sĩ số:** {class_info.get('Quantity')} sinh viên
                - **Học kỳ:** {class_info.get('Semester')}
                - **Thời gian:** {class_info.get('DateStart')} → {class_info.get('DateEnd')}
                """)
                
            elif resp.status_code == 400:
                # Lỗi mã lớp trùng hoặc validation
                try:
                    error_json = resp.json()
                    error_msg = error_json.get("detail", resp.text)
                except:
                    error_msg = resp.text
                st.error(f"{error_msg}")
                
            elif resp.status_code == 0:
                st.error(f"{resp.text}")
            else:
                try:
                    error_json = resp.json()
                    error_msg = error_json.get("detail", resp.text)
                except:
                    error_msg = resp.text
                st.error(f"Lỗi {resp.status_code}: {error_msg}")