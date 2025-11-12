import streamlit as st
from pathlib import Path
from services.api_client import get_majors, get_types, get_shifts, create_class

# Cấu hình trang
st.set_page_config(page_title="THÊM LỚP HỌC", layout="wide")

# Load css
add_class_css_path = Path(__file__).parent.parent / "public" / "css" / "add_class.css"
if add_class_css_path.exists():
    with open(add_class_css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("<h2>THÊM LỚP HỌC</h2>", unsafe_allow_html=True)
st.markdown('<div class="note">Bạn đã có lớp của mình? <span>Tại đây</span></div>', unsafe_allow_html=True)

# Lấy dữ liệu từ backend
majors = get_majors()
types = get_types()
shifts = get_shifts()

major_options = {str(m['MajorID']): m['MajorName'] for m in majors}
type_options = {str(t['TypeID']): t['TypeName'] for t in types}
shift_options = {str(s['ShiftID']): s['ShiftName'] for s in shifts}

# --- CHỈ NHỮNG TRƯỜNG TẠO MÃ (đặt ngoài form để cập nhật ngay) ---
col1, col2, col3 = st.columns([2,2,1])
with col1:
    selected_major = st.selectbox("Chọn chuyên ngành", options=list(major_options.keys()),
                                  format_func=lambda x: major_options[x] if x in major_options else "", key="major")
with col2:
    selected_type = st.selectbox("Chọn loại", options=list(type_options.keys()),
                                 format_func=lambda x: type_options[x] if x in type_options else "", key="type")
with col3:
    year = st.text_input("Năm", max_chars=4, key="year")

col4, col5, col6 = st.columns([1,2,1])
with col5:
    class_code = st.text_input("Mã học phần", max_chars=20, key="class_code")
with col6:
    quantity = st.number_input("Sĩ số", min_value=1, max_value=999, step=1, key="quantity")

# Tạo mã lớp (mã rút gọn) và hiển thị TRỰC TIẾP trong ô "Mã lớp"
if year and class_code and selected_major:
    short_code_val = f"{year[-2:]}{major_options[selected_major][:2].upper()}{class_code[-2:]}"
else:
    short_code_val = ""

colA, colB = st.columns([1,3])
with colA:
    st.text_input("Mã lớp", value=short_code_val, max_chars=10, key="short_code", disabled=True)
with colB:
    st.write("")  # placeholder to giữ layout

# Các trường còn lại có thể để trong form để group lại và validate trước khi gửi
with st.form("add_class_form"):
    teacher_name = st.text_input("Nhập tên giảng viên", key="teacher_name")
    semester = st.selectbox("Học kỳ", options=["Học kỳ 1", "Học kỳ 2", "Học kỳ 3"], key="semester")
    date_start = st.date_input("Start", key="date_start")
    date_end = st.date_input("End", key="date_end")
    weekday = st.text_input("Thứ học", key="weekday", disabled=True)
    selected_shift = st.selectbox("Ca học", options=list(shift_options.keys()),
                                  format_func=lambda x: shift_options[x] if x in shift_options else "", key="shift")
    subject_name = st.text_input("Nhập tên môn học", key="subject_name")

    submitted = st.form_submit_button("SAVE")
    if submitted:
        # validate
        if not (year and class_code and selected_major and teacher_name and subject_name):
            st.error("Vui lòng nhập đầy đủ thông tin bắt buộc!")
        else:
            payload = {
                "class_name": short_code_val,        # classname trong DB
                "full_class_name": class_code,      # mã học phần
                "quantity": int(quantity),
                "semester": semester,
                "date_start": str(date_start),
                "date_end": str(date_end),
                "session": weekday,
                "teacher_class": teacher_name,
                "type_id": int(selected_type),
                "major_id": int(selected_major),
                "shift_id": int(selected_shift),
                "subject_name": subject_name
            }
            resp = create_class(payload)
            if resp is not None and resp.status_code in (200, 201):
                st.success("Lưu lớp học thành công!")
            else:
                st.error(f"Lưu lớp thất bại: {getattr(resp, 'text', 'No response')}")