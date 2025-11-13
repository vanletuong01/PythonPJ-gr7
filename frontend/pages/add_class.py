import streamlit as st
from pathlib import Path
import datetime
from services.api_client import get_majors, get_types, get_shifts, create_class

st.set_page_config(page_title="THÊM LỚP HỌC", layout="wide")

# Load CSS
add_class_css_path = Path(__file__).parent.parent / "public" / "css" / "add_class.css"
if add_class_css_path.exists():
    with open(add_class_css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

majors = get_majors() or []
types = get_types() or []
shifts = get_shifts() or []

major_options = {str(m['MajorID']): m['MajorName'] for m in majors}
type_options = {str(t['TypeID']): t['TypeName'] for t in types}
shift_options = {str(s['ShiftID']): s['ShiftName'] for s in shifts}

col_left, col_right = st.columns([1.2, 2])

with col_left:
    avatar_path = Path(__file__).parent.parent / "public" / "images" / "avatar.png"
    if avatar_path.exists():
        st.image(str(avatar_path), width=60)
    else:
        st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)

    teacher_name = st.session_state.get("teacher", {}).get("name", "Tên giáo viên")
    st.markdown(f"""
        <div style="font-weight:600; font-size:18px; margin-top:10px;">{teacher_name}</div>
    """, unsafe_allow_html=True)

    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=180)

    st.markdown("""
        <div style="font-size:22px; font-weight:700; margin-top:10px;">VIETNAM AVIATION ACADEMY</div>
        <div style="font-size:18px; font-weight:500; margin-bottom:20px;">Học Viện Hàng Không Việt Nam</div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="font-size:13px; color:#888; margin-top:40px;">
            Trang điểm danh sinh viên
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("<h2 style='margin-bottom:0;'>← THÊM LỚP HỌC</h2>", unsafe_allow_html=True)

    col_major, col_type, col_year = st.columns([2,2,1])
    with col_major:
        selected_major = st.selectbox("Chọn chuyên ngành", options=list(major_options.keys()),
                                      format_func=lambda x: major_options[x] if x in major_options else "")
    with col_type:
        selected_type = st.selectbox("Chọn loại", options=list(type_options.keys()),
                                     format_func=lambda x: type_options[x] if x in type_options else "")
    with col_year:
        year = st.text_input("Năm", max_chars=4)

    col_code, col_class, col_quantity = st.columns([2,3,1])
    with col_code:
        major_code = st.text_input("___", "")
    with col_class:
        class_code = st.text_input("Mã học phần:", "")
    with col_quantity:
        quantity = st.text_input("Sĩ số:", "")

    def generate_short_class_name(year, major_code, class_code):
        return f"{year[-2:]}{major_code}{class_code[-2:]}" if year and major_code and class_code else ""
    shortcode = generate_short_class_name(year, major_code, class_code)
    st.text_input("Shortcode lớp học:", value=shortcode, disabled=True)

    teacher = st.text_input("Nhập tên giảng viên:", "")
    semester = st.selectbox("Học kỳ", ["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"], index=0)

    col_start, col_end, col_weekday = st.columns([2,2,1])
    with col_start:
        date_start = st.date_input("Start:")
    with col_end:
        date_end = st.date_input("End:")
    with col_weekday:
        weekday_num = date_start.weekday()
        weekday_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        weekday_str = weekday_vn[weekday_num]
        st.text_input("Thứ học:", weekday_str, disabled=True)

    shift = st.selectbox("Ca học", options=list(shift_options.keys()),
                         format_func=lambda x: shift_options[x] if x in shift_options else "")
    subject = st.text_input("Nhập tên môn học:")

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    save_btn = st.button("SAVE")

    if save_btn:
        data = {
            "major": major_options.get(selected_major, ""),      # gửi tên chuyên ngành
            "type": type_options.get(selected_type, ""),         # gửi tên loại hình
            "year": year,
            "major_code": major_code,
            "class_code": class_code,
            "quantity": quantity,
            "teacher_class": teacher,
            "semester": semester,
            "date_start": str(date_start),
            "date_end": str(date_end),
            "weekday": weekday_str,
            "shift": shift_options.get(shift, ""),               # gửi tên ca học
            "class_name": shortcode,
            "full_class_name": f"{year}-{major_code}-{class_code}",
            "subject": subject
        }
        resp = create_class(data)
        if resp and getattr(resp, "status_code", None) == 200:
            st.success("Tạo lớp học thành công!")
        else:
            st.error("Tạo lớp học thất bại!")
    st.markdown(
        '<div class="note" style="margin-top:24px;">Bạn đã có lớp của mình? <span style="color:#e74c3c;">Tại đây</span></div>',
        unsafe_allow_html=True
    )
