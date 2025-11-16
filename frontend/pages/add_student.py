import streamlit as st
from datetime import date
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import create_student, search_students, get_classes, get_majors, get_types

st.set_page_config(page_title="Thêm Sinh Viên", page_icon="👨‍🎓", layout="wide")
render_header()
render_dashboard_sidebar()

# Load data
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []
def to_opts(items, idk, namek):
    return {str(i.get(namek)): int(i.get(idk)) for i in items if isinstance(i, dict) and i.get(idk)}
major_opts = to_opts(majors, "MajorID", "MajorName")
class_opts = to_opts(classes, "ClassID", "ClassName")
type_opts  = to_opts(types, "TypeID", "TypeName")
years = [f"K{i}" for i in range(45, 75)]

# Top bar: title + search + button
col_title, col_search, col_btn = st.columns([1.2, 1.4, 0.8])
with col_title:
    st.markdown('<div class="page-title">← THÊM SINH VIÊN</div>', unsafe_allow_html=True)
with col_search:
    search_q = st.text_input("", key="search_input", placeholder="Tìm kiếm", label_visibility="collapsed")
with col_btn:
    st.markdown('<button class="btn-pink">Thêm sinh viên mới</button>', unsafe_allow_html=True)

# Kết quả tìm kiếm (nếu có)
if search_q and len(search_q.strip()) >= 2:
    st.markdown('<div class="search-results">', unsafe_allow_html=True)
    try:
        res = search_students(search_q.strip())
        rows = res.get("data", []) if isinstance(res, dict) else res
        if rows:
            st.dataframe(
                [{"MSSV": r.get("StudentCode"), "Họ tên": r.get("FullName"), "Lớp": r.get("ClassID")} for r in rows],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Không tìm thấy")
    except Exception as e:
        st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

# Filters
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1: year = st.selectbox("Khóa", years, key="f_year")
with fc2: major_lbl = st.selectbox("Ngành", list(major_opts.keys()) or ["--"], key="f_major")
with fc3: type_lbl = st.selectbox("Loại", list(type_opts.keys()) or ["--"], key="f_type")
with fc4: mssv = st.text_input("Mssv", key="f_mssv")

# Form card
st.markdown('<div class="form-card">', unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)
with r1c1: fullname = st.text_input("Họ tên:", key="inp_name")
with r1c2: phone = st.text_input("SDT:", key="inp_phone")

r2c1, r2c2 = st.columns(2)
with r2c1: class_lbl = st.selectbox("Lớp:", list(class_opts.keys()) or ["--"], key="inp_class")
with r2c2: cccd = st.text_input("CCCD:", key="inp_cccd")

dob = st.date_input("Date:", value=date(2005, 4, 20), key="inp_dob")

if st.button("SAVE", type="primary", use_container_width=True):
    if not fullname or not mssv:
        st.error("Thiếu họ tên hoặc MSSV")
    else:
        payload = {
            "FullName": fullname.strip(),
            "StudentCode": mssv.strip(),
            "DefaultClass": class_opts.get(class_lbl),
            "ClassID": class_opts.get(class_lbl),
            "Phone": phone.strip(),
            "AcademicYear": year,
            "DateOfBirth": str(dob),
            "CitizenID": cccd.strip(),
            "MajorID": major_opts.get(major_lbl),
            "TypeID": type_opts.get(type_lbl),
            "PhotoStatus": "NONE"
        }
        try:
            r = create_student(payload)
            st.success("✔ Thêm thành công") if r.get("success") else st.error(r.get("message"))
        except Exception as ex:
            st.error(str(ex))

st.markdown('</div>', unsafe_allow_html=True)

# Status buttons
st.markdown("### Trạng thái ảnh:")
sb1, sb2, sb3 = st.columns(3)
with sb1: st.button("NONE", key="s_none")
with sb2: st.button("Lấy ảnh sinh viên", key="s_capture")
with sb3: st.button("Training data", key="s_train")
