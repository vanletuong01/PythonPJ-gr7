import streamlit as st
from datetime import date, datetime
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import create_student, search_students, get_classes, get_majors, get_types

st.set_page_config(page_title="Thêm Sinh Viên", layout="wide")

selected_class_id = st.session_state.get("selected_class_id")
class_info = None
if selected_class_id is not None:
    classes = get_classes()
    class_info = next((c for c in classes if c.get("ClassID") == selected_class_id), None)

if class_info:
    render_header(
        class_name=class_info.get("ClassName", ""),
        full_class_name=class_info.get("FullClassName", ""),
        course_code=class_info.get("CourseCode", "")
    )
else:
    render_header()

render_dashboard_sidebar()

# Load data
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []
def to_opts(items, idk, namek):
    return {str(i.get(idk)): i.get(namek) for i in items if isinstance(i, dict) and i.get(idk)}
major_opts = to_opts(majors, "MajorID", "MajorName")
class_opts = to_opts(classes, "ClassID", "ClassName")
type_opts  = to_opts(types, "TypeID", "TypeName")

# Tạo danh sách năm từ 2000 đến năm hiện tại
current_year = datetime.now().year
years = [str(y) for y in range(2000, current_year + 1)]

# Top bar: title + search + button
col_title, col_search, col_btn = st.columns([1.2, 1.4, 0.8])
with col_title:
    st.markdown('<div class="page-title">← THÊM SINH VIÊN</div>', unsafe_allow_html=True)
with col_search:
    search_q = st.text_input("Tìm kiếm sinh viên", key="search_input", placeholder="Tìm kiếm", label_visibility="collapsed")
with col_btn:
    st.markdown('<button class="btn-pink">Thêm sinh viên mới</button>', unsafe_allow_html=True)

if search_q and len(search_q.strip()) >= 2:
    try:
        res = search_students(search_q.strip())
        rows = res.get("data", []) if isinstance(res, dict) else res
        if rows:
            sv = rows[0]
            st.session_state["inp_name"] = sv.get("FullName", "")
            st.session_state["f_mssv"] = sv.get("StudentCode", "")
            st.session_state["inp_class"] = str(sv.get("DefaultClass", ""))
            st.session_state["inp_phone"] = sv.get("Phone", "")
            # Xử lý ngày sinh từ chuỗi sang date
            dob_val = sv.get("DateOfBirth")
            if isinstance(dob_val, str):
                try:
                    dob_val = datetime.strptime(dob_val, "%Y-%m-%d").date()
                except Exception:
                    dob_val = None
            st.session_state["inp_dob"] = dob_val
            st.session_state["inp_cccd"] = sv.get("CitizenID", "")
            st.session_state["f_year"] = sv.get("AcademicYear", "")
            # Lấy tên ngành và loại từ id (so sánh kiểu str)
            major_id = str(sv.get("MajorID", ""))
            type_id = str(sv.get("TypeID", ""))
            st.session_state["f_major"] = major_opts.get(major_id, "")
            st.session_state["f_type"] = type_opts.get(type_id, "")
            st.session_state["photo_status"] = "Yes" if sv.get("PhotoStatus") else "None"
        else:
            st.info("Không tìm thấy")
    except Exception as e:
        st.error(str(e))

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    # Sử dụng key khác cho dropdown để tránh ghi đè với session_state["f_year"]
    if st.session_state.get("f_year") and str(st.session_state.get("f_year")) in years:
        st.text(f"Khóa: {st.session_state.get('f_year', '')}")
        academic_year = str(st.session_state.get('f_year', ''))
    else:
        academic_year = st.selectbox("Khóa", options=years, key="select_year")

with fc2:
    if st.session_state.get("f_major"): 
        st.text(f"Ngành: {st.session_state.get('f_major', '')}")
        major_lbl = st.session_state.get('f_major', '')
    else: 
        major_lbl = st.selectbox("Ngành", list(major_opts.values()) or ["--"], key="f_major")

with fc3:
    if st.session_state.get("f_type"):
        st.text(f"Loại: {st.session_state.get('f_type', '')}")
        type_lbl = st.session_state.get('f_type', '')
    else:
        type_lbl = st.selectbox("Loại", list(type_opts.values()) or ["--"], key="f_type")

with fc4:
    mssv = st.text_input("MSSV", key="f_mssv")

st.markdown('<div class="form-card">', unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)
with r1c1: fullname = st.text_input("Họ tên:", key="inp_name")
with r1c2: phone = st.text_input("SDT:", key="inp_phone")

r2c1, r2c2 = st.columns(2)
with r2c1: class_lbl = st.text_input("Lớp:", key="inp_class")
with r2c2: cccd = st.text_input("CCCD:", key="inp_cccd")

# Ngày sinh
dob_val = st.session_state.get("inp_dob")
if isinstance(dob_val, str):
    try:
        dob_val = datetime.strptime(dob_val, "%Y-%m-%d").date()
    except Exception:
        dob_val = date(2005, 1, 1)
elif not isinstance(dob_val, date) or dob_val is None:
    dob_val = date(2005, 1, 1)

dob = st.date_input(
    "Ngày sinh:",
    value=dob_val,
    key="inp_dob",
    min_value=date(1900, 1, 1),
    max_value=date(2100, 12, 31)
)

# Trạng thái ảnh
st.text(f"Trạng thái ảnh: {st.session_state.get('photo_status', 'None')}")

if st.button("SAVE", type="primary", use_container_width=True):
    if not fullname or not mssv:
        st.error("Thiếu họ tên hoặc MSSV")
    else:
        # Lấy id từ tên ngành/loại/lớp
        major_id = next((int(k) for k, v in major_opts.items() if v == major_lbl), None)
        type_id = next((int(k) for k, v in type_opts.items() if v == type_lbl), None)
        class_id = next((int(k) for k, v in class_opts.items() if v == class_lbl), None)
        # Lấy giá trị năm từ academic_year (dropdown hoặc tìm kiếm)
        payload = {
            "FullName": fullname.strip(),
            "StudentCode": mssv.strip(),
            "DefaultClass": class_lbl.strip(),
            "ClassID": class_id,
            "Phone": phone.strip() if phone else "",
            "AcademicYear": academic_year,
            "DateOfBirth": dob.isoformat() if dob else "",
            "CitizenID": cccd.strip() if cccd else "",
            "FullName": fullname.strip() if fullname else "",
            "StudentCode": mssv.strip() if mssv else "",
            "DefaultClass": class_lbl.strip() if class_lbl else "",
            "ClassID": class_id,
            "Phone": phone.strip() if phone else "",
            "AcademicYear": academic_year,
            "DateOfBirth": dob.isoformat() if dob else "",
            "CitizenID": cccd.strip() if cccd else "",
            "MajorID": major_id,
            "TypeID": type_id,
            "PhotoStatus": "NONE"
        }
        try:
            r = create_student(payload)
            if r.get("success"):
                st.success("Thêm thành công")
                # Reset các trường nhập liệu
                for k in ["inp_name", "f_mssv", "inp_class", "inp_phone", "inp_cccd", "inp_dob"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
            else:
                st.error(r.get("message"))
        except Exception as ex:
            st.error(str(ex))

st.markdown('</div>', unsafe_allow_html=True)

# Status buttons
st.markdown("### Trạng thái ảnh:")
sb1, sb2, sb3 = st.columns(3)
with sb1: 
    st.button("NONE", key="s_none")
with sb2: 
    if st.button("Lấy ảnh sinh viên", key="s_capture"):
        current_mssv = (mssv or "").strip()
        current_name = (fullname or "").strip()
        if not current_mssv:
            st.error("⚠ Vui lòng nhập MSSV trước khi chụp ảnh")
        elif not current_name:
            st.error("⚠ Vui lòng nhập Họ tên trước khi chụp ảnh")
        else:
            st.session_state["capture_mssv"] = current_mssv
            st.session_state["capture_name"] = current_name
            try:
                st.query_params["code"] = current_mssv
                st.query_params["name"] = current_name
            except:
                st.experimental_set_query_params(code=current_mssv, name=current_name)
            st.switch_page("pages/capture_photo.py")
with sb3: 
    st.button("Training data", key="s_train")
