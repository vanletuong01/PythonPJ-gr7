import streamlit as st
from pathlib import Path
from services.api_client import get_majors, get_types, get_shifts

# Cấu hình trang
st.set_page_config(
    page_title="Đăng nhập - VAA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

add_class_css_path = Path(__file__).parent.parent / "public" / "css" / "add_class.css"
if add_class_css_path.exists():
    with open(add_class_css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])

st.markdown("<h2 style='margin-bottom:0;'>THÊM LỚP HỌC</h2>", unsafe_allow_html=True)
st.markdown('<div class="note">Bạn đã có lớp của mình? <span>Tại đây</span></div>', unsafe_allow_html=True)

majors = get_majors()
types = get_types()
shifts = get_shifts()

major_options = {str(m['MajorID']): m['MajorName'] for m in majors}
type_options = {str(t['TypeID']): t['TypeName'] for t in types}
shift_options = {str(s['ShiftID']): s['ShiftName'] for s in shifts}

with st.form("add_class_form"):
    st.markdown('<div class="add-class-form">', unsafe_allow_html=True)

    # Dòng 1: Chuyên ngành, loại, năm
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        selected_major = st.selectbox("Chọn chuyên ngành", options=list(major_options.keys()), format_func=lambda x: major_options[x], key="major")
    with col2:
        selected_type = st.selectbox("Chọn loại", options=list(type_options.keys()), format_func=lambda x: type_options[x], key="type")
    with col3:
        year = st.text_input("Năm", max_chars=4, key="year")

    # Dòng 2: Mã lớp, mã học phần, sĩ số
    col4, col5, col6 = st.columns([1,2,1])
    with col5:
        class_code = st.text_input("Mã học phần", max_chars=20, key="class_code")
    with col6:
        quantity = st.number_input("Sĩ số", min_value=1, max_value=999, step=1, key="quantity")
    with col4:
        if year and class_code and selected_major:
            short_code_val = f"{year[-2:]}{major_options[selected_major][:2].upper()}{class_code[-2:]}"
        else:
            short_code_val = ""
        st.text_input("Mã lớp", value=short_code_val, max_chars=10, key="short_code", disabled=True)
    # Dòng 3: Tên giảng viên, học kỳ
    col7, col8 = st.columns([3,1])
    with col7:
        teacher_name = st.text_input("Nhập tên giảng viên", key="teacher_name")
    with col8:
        semester = st.selectbox("Học kỳ", options=["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"], key="semester")

    # Dòng 4: Start, End, Thứ học, Ca học
    col9, col10, col11, col12 = st.columns([1,1,1,1])
    with col9:
        date_start = st.date_input("Start", key="date_start")
    with col10:
        date_end = st.date_input("End", key="date_end")
    with col11:
        weekday = st.text_input("Thứ học", key="weekday", disabled=True)
    with col12:
        selected_shift = st.selectbox("Ca học", options=list(shift_options.keys()), format_func=lambda x: shift_options[x], key="shift")

    # Dòng 5: Tên môn học
    subject_name = st.text_input("Nhập tên môn học", key="subject_name")

    # Nút Save
    submitted = st.form_submit_button("SAVE")
    if submitted:
        # Kiểm tra dữ liệu bắt buộc
        if not (year and class_code and selected_major and teacher_name and subject_name):
            st.error("Vui lòng nhập đầy đủ thông tin bắt buộc!")
        else:
            # Gửi dữ liệu lên backend ở đây
            st.success("Lưu lớp học thành công!")