import streamlit as st
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from datetime import date
import requests

# API client
from services.api_client import (
    get_majors,
    get_classes,
    get_types,
    create_student as api_create_student
)

st.set_page_config(
    page_title="Thêm Sinh Viên",
    page_icon="👨‍🎓",
    layout="wide"
)

# Render UI
render_header()
render_dashboard_sidebar()

# ================== LOAD BACKEND DATA ================== #
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []
academic_years = ["K45", "K46", "K47", "K48"]

# Convert to selectbox options
def to_options(items, id_key, name_key):
    opts = {}
    for item in items:
        if isinstance(item, dict) and id_key in item and name_key in item:
            opts[str(item[name_key])] = int(item[id_key])
    return opts

major_options = to_options(majors, "MajorID", "MajorName")
class_options = to_options(classes, "ClassID", "ClassName")
type_options = to_options(types, "TypeID", "TypeName")

# ================== UI RENDER ================== #
st.markdown("""
    <div class="page-title">← THÊM SINH VIÊN</div>
    <div class="page-subtitle">
        Sinh viên đã có thông tin? 
        <a href="#">Tại đây</a>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="form-card">', unsafe_allow_html=True)

# ----------------- FORM ----------------- #
col1, col2, col3 = st.columns([2, 1.5, 1])
with col1:
    full_name = st.text_input("Họ tên:")
with col2:
    student_code = st.text_input("Mã sinh viên (MSSV):")
with col3:
    academic_year = st.selectbox("Khóa", academic_years)

col4, col5, col6 = st.columns([1.5, 1.5, 1])
with col4:
    class_label = st.selectbox("Lớp", list(class_options.keys()) or ["-- Chưa có lớp --"])
with col5:
    phone = st.text_input("Số điện thoại:")
with col6:
    major_label = st.selectbox("Ngành", list(major_options.keys()) or ["-- Chưa có ngành --"])

col7, col8, col9 = st.columns([1.5, 1.5, 1])
with col7:
    dob = st.date_input("Ngày sinh:", value=date(2005, 4, 20))
with col8:
    citizen_id = st.text_input("CCCD:")
with col9:
    type_label = st.selectbox("Loại", list(type_options.keys()) or ["-- Chưa có loại --"])

# Ảnh sinh viên
uploaded_img = st.file_uploader("Ảnh sinh viên", type=["png", "jpg", "jpeg"])

# ================== SAVE BUTTON ================== #
if st.button("SAVE", type="primary"):

    if not full_name or not student_code:
        st.error("Vui lòng nhập họ tên và MSSV.")
    else:
        payload = {
            "FullName": full_name,
            "StudentCode": student_code,
            "DefaultClass": class_options.get(class_label),
            "Phone": phone,
            "AcademicYear": academic_year,
            "DateOfBirth": str(dob),
            "CitizenID": citizen_id,
            "MajorID": major_options.get(major_label),
            "TypeID": type_options.get(type_label),   # FIX QUAN TRỌNG
            "ClassID": class_options.get(class_label),
            "PhotoStatus": "NONE",
            "StudentPhoto": None
        }

        # gửi ảnh nếu có
        files = {}
        if uploaded_img is not None:
            files = {
                "StudentPhoto": (uploaded_img.name, uploaded_img.getvalue())
            }

        try:
            # Nếu có hàm trong api_client thì dùng
            if api_create_student:
                res = api_create_student(payload, uploaded_img)
            else:
                r = requests.post(
                    "http://127.0.0.1:8000/api/v1/student/create",
                    data=payload,
                    files=files,
                    timeout=10
                )
                res = r.json()
        except Exception as e:
            res = {"success": False, "message": str(e)}

        if res.get("success"):
            st.success("✔ Thêm sinh viên thành công!")
        else:
            st.error("❌ Lỗi: " + str(res.get("message", "Unknown error")))

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Tabs ---------------- #
st.markdown("""
<div class="tab-container">
    <div class="tab-title">Trạng thái ảnh:</div>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1, 1, 1])
col_a.button("NONE")
col_b.button("Lấy ảnh sinh viên")
col_c.button("Training data")
