import streamlit as st
from datetime import date, datetime
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import (
    create_student,
    search_students,
    get_classes,
    get_majors,
    get_types,
    assign_student_to_class
)

st.set_page_config(page_title="Thêm Sinh Viên", layout="wide")

# Lấy class đã chọn ở trang trước
selected_class_id = st.session_state.get("selected_class_id")
class_info = None
if selected_class_id:
    classes = get_classes() or []
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

# Load dữ liệu dropdown
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []


def to_opts(items, idk, namek):
    return {str(i[idk]): i[namek] for i in items if isinstance(i, dict) and i.get(idk)}


major_opts = to_opts(majors, "MajorID", "MajorName")
class_opts = to_opts(classes, "ClassID", "ClassName")
type_opts = to_opts(types, "TypeID", "TypeName")

# Năm học
current_year = datetime.now().year
years = [str(y) for y in range(2000, current_year + 1)]

# ------- TOP BAR -------
col_title, col_search, col_btn = st.columns([1.2, 1.4, 0.8])
with col_title:
    st.markdown('<div class="page-title">← THÊM SINH VIÊN</div>', unsafe_allow_html=True)

with col_search:
    search_q = st.text_input(
        "Tìm kiếm sinh viên",
        key="search_input",
        placeholder="Tìm theo tên hoặc MSSV...",
        label_visibility="collapsed"
    )

with col_btn:
    st.markdown('<button class="btn-pink">Thêm sinh viên mới</button>', unsafe_allow_html=True)

# ------- KHI TÌM KIẾM -------
if search_q and len(search_q.strip()) >= 2:
    try:
        res = search_students(search_q.strip())
        rows = res.get("data", []) if isinstance(res, dict) else res

        if rows:
            sv = rows[0]

            # LƯU StudentID để dùng khi assign
            st.session_state["found_student_id"] = sv.get("StudentID") or sv.get("student_id") or sv.get("id")

            st.session_state["inp_name"] = sv.get("FullName", "")
            st.session_state["f_mssv"] = sv.get("StudentCode", "")
            st.session_state["inp_class"] = str(sv.get("DefaultClass", ""))
            st.session_state["inp_phone"] = sv.get("Phone", "")
            st.session_state["inp_cccd"] = sv.get("CitizenID", "")
            st.session_state["f_year"] = str(sv.get("AcademicYear", ""))
            st.session_state["photo_status"] = "Yes" if sv.get("PhotoStatus") else "None"

            # Ngày sinh
            dob_raw = sv.get("DateOfBirth")
            try:
                dob_val = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except:
                dob_val = None
            st.session_state["inp_dob"] = dob_val

            # Major + Type
            st.session_state["f_major"] = major_opts.get(str(sv.get("MajorID", "")), "")
            st.session_state["f_type"] = type_opts.get(str(sv.get("TypeID", "")), "")

        else:
            # xóa student_id nếu không tìm thấy
            if "found_student_id" in st.session_state:
                del st.session_state["found_student_id"]
            st.info("Không tìm thấy sinh viên!")

    except Exception as e:
        st.error(str(e))

# ------- FORM -------
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    if str(st.session_state.get("f_year", "")) in years:
        st.text(f"Khóa: {st.session_state['f_year']}")
        academic_year = st.session_state["f_year"]
    else:
        academic_year = st.selectbox("Khóa", years, key="select_year")

with fc2:
    if st.session_state.get("f_major"):
        st.text(f"Ngành: {st.session_state['f_major']}")
        major_lbl = st.session_state["f_major"]
    else:
        major_lbl = st.selectbox("Ngành", list(major_opts.values()), key="inp_major")

with fc3:
    if st.session_state.get("f_type"):
        st.text(f"Loại: {st.session_state['f_type']}")
        type_lbl = st.session_state["f_type"]
    else:
        type_lbl = st.selectbox("Loại", list(type_opts.values()), key="inp_type")

with fc4:
    mssv = st.text_input("MSSV", key="f_mssv")

st.markdown('<div class="form-card">', unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)
with r1c1:
    fullname = st.text_input("Họ tên:", key="inp_name")
with r1c2:
    phone = st.text_input("SDT:", key="inp_phone")

r2c1, r2c2 = st.columns(2)
with r2c1:
    class_lbl = st.text_input("Lớp:", key="inp_class")
with r2c2:
    cccd = st.text_input("CCCD:", key="inp_cccd")

# Ngày sinh
dob_val = st.session_state.get("inp_dob")
if not isinstance(dob_val, date):
    dob_val = date(2005, 1, 1)

dob = st.date_input("Ngày sinh:", value=dob_val, key="inp_dob")

# Trạng thái ảnh
st.text(f"Trạng thái ảnh: {st.session_state.get('photo_status', 'None')}")

# =========================================================
#                      SAVE BUTTON
# =========================================================
if st.button("SAVE", type="primary", use_container_width=True):

    if not mssv:
        st.error("⚠ Thiếu MSSV")
        st.stop()

    if not selected_class_id:
        st.error("⚠ Chưa chọn lớp. Vui lòng chọn lớp trước khi lưu.")
        st.stop()

    # Kiểm tra sinh viên có phải là kết quả tìm kiếm hay không
    is_existing = (
        st.session_state.get("search_input")
        and st.session_state.get("f_mssv") == mssv
    )

    # -------------------------------------------------------------
    # TRƯỜNG HỢP 1: ĐÃ CÓ SINH VIÊN → GÁN VÀO LỚP
    # -------------------------------------------------------------
    if is_existing:
        found_id = st.session_state.get("found_student_id")
        # Nếu không có student_id (hiếm) -> thử gọi search lại để lấy id
        if not found_id:
            try:
                res = search_students(mssv, limit=1)
                rows = res.get("data", []) if isinstance(res, dict) else res
                if rows:
                    found_id = rows[0].get("StudentID") or rows[0].get("student_id") or rows[0].get("id")
                    st.session_state["found_student_id"] = found_id
            except Exception as e:
                st.error(f"Lỗi khi tìm lại StudentID: {e}")
                st.stop()

        if not found_id:
            st.error("Không xác định được StudentID của sinh viên đã tìm; không thể gán.")
            st.stop()

        try:
            assign_student_to_class(student_id=int(found_id), class_id=int(selected_class_id))
            st.success("Đã gán sinh viên vào lớp thành công!")
            st.rerun()

        except Exception as e:
            st.error(f"Lỗi khi gán sinh viên vào lớp: {e}")

        st.stop()

    # -------------------------------------------------------------
    # TRƯỜNG HỢP 2: TẠO SINH VIÊN MỚI + GÁN VÀO LỚP
    # -------------------------------------------------------------

    major_id = next((int(k) for k, v in major_opts.items() if v == major_lbl), None)
    type_id = next((int(k) for k, v in type_opts.items() if v == type_lbl), None)

    student_payload = {
        "FullName": fullname,
        "StudentCode": mssv,
        "DefaultClass": class_lbl,
        "Phone": phone if phone else None,
        "AcademicYear": academic_year,
        "DateOfBirth": dob.isoformat(),
        "CitizenID": cccd,
        "MajorID": major_id,
        "TypeID": type_id,
        "PhotoStatus": "NONE",
        "StudentPhoto": None
    }

    try:
        # 1. Tạo sinh viên
        created = create_student(student_payload)

        # Try to extract new StudentID from response
        new_id = None
        if isinstance(created, dict):
            new_id = created.get("StudentID") or created.get("student_id") or created.get("id")
        else:
            new_id = getattr(created, "StudentID", None) or getattr(created, "student_id", None)

        if not new_id:
            st.error("Tạo sinh viên xong nhưng không nhận được StudentID từ backend.")
            st.stop()

        # 2. Gán vào lớp bằng StudentID
        assign_student_to_class(student_id=int(new_id), class_id=int(selected_class_id))

        st.success("Tạo và gán sinh viên vào lớp thành công!")
        # xóa các trường tạm trong session_state để làm mới form
        for k in ["inp_name", "f_mssv", "inp_class", "inp_phone", "inp_cccd", "inp_dob", "found_student_id"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    except Exception as e:
        st.error(f"Lỗi khi tạo hoặc gán sinh viên: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# ẢNH
# -------------------------------------------------------------
st.markdown("### Trạng thái ảnh:")

sb1, sb2, sb3 = st.columns(3)

with sb1:
    st.button("NONE", key="s_none")

with sb2:
    if st.button("Lấy ảnh sinh viên", key="s_capture"):
        if not mssv:
            st.error("⚠ Nhập MSSV trước khi chụp ảnh")
        elif not fullname:
            st.error("⚠ Nhập tên sinh viên trước khi chụp ảnh")
        else:
            st.session_state["capture_mssv"] = mssv.strip()
            st.session_state["capture_name"] = fullname.strip()

            try:
                st.query_params["code"] = mssv
                st.query_params["name"] = fullname
            except:
                st.experimental_set_query_params(code=mssv, name=fullname)

            st.switch_page("pages/capture_photo.py")

with sb3:
    st.button("Training data", key="s_train")
