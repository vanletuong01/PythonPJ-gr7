import streamlit as st
from datetime import date, datetime
from pathlib import Path
import sys

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
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

# ===== LOAD CSS (NẾU CẦN) =====
# Dùng lại CSS của student_detail hoặc tạo file css riêng add_student.css
css_path = Path(__file__).parent.parent / "public" / "css" / "student_detail.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== HEADER & SIDEBAR =====
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

# ===== DATA LOADING =====
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []

def to_opts(items, idk, namek):
    return {str(i[idk]): i[namek] for i in items if isinstance(i, dict) and i.get(idk)}

major_opts = to_opts(majors, "MajorID", "MajorName")
class_opts = to_opts(classes, "ClassID", "ClassName")
type_opts = to_opts(types, "TypeID", "TypeName")

current_year = datetime.now().year
years = [str(y) for y in range(2000, current_year + 1)]

# ===== TOP BAR: TIÊU ĐỀ & TÌM KIẾM =====
col_title, col_search = st.columns([1, 2])
with col_title:
    # Nút quay lại Dashboard
    if st.button("⬅️ Về Dashboard", key="btn_back_dash"):
        st.switch_page("dashboard.py")
    st.markdown("### THÊM SINH VIÊN MỚI")

with col_search:
    search_q = st.text_input(
        "Tìm kiếm sinh viên (để gán vào lớp)",
        key="search_input",
        placeholder="Nhập tên hoặc MSSV để tìm..."
    )

# ===== LOGIC TÌM KIẾM =====
if search_q and len(search_q.strip()) >= 2:
    try:
        res = search_students(search_q.strip())
        rows = res.get("data", []) if isinstance(res, dict) else res

        if rows:
            sv = rows[0]
            st.session_state["found_student_id"] = sv.get("StudentID") or sv.get("student_id")
            st.session_state["inp_name"] = sv.get("FullName", "")
            st.session_state["f_mssv"] = sv.get("StudentCode", "")
            st.session_state["inp_class"] = str(sv.get("DefaultClass", ""))
            st.session_state["inp_phone"] = sv.get("Phone", "")
            st.session_state["inp_cccd"] = sv.get("CitizenID", "")
            st.session_state["f_year"] = str(sv.get("AcademicYear", ""))
            st.session_state["photo_status"] = "Yes" if sv.get("PhotoStatus") else "None"
            
            dob_raw = sv.get("DateOfBirth")
            try:
                dob_val = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except:
                dob_val = None
            st.session_state["inp_dob"] = dob_val
            
            st.session_state["f_major"] = major_opts.get(str(sv.get("MajorID", "")), "")
            st.session_state["f_type"] = type_opts.get(str(sv.get("TypeID", "")), "")
            st.success("Đã tìm thấy sinh viên! Kiểm tra thông tin bên dưới.")
        else:
            if "found_student_id" in st.session_state:
                del st.session_state["found_student_id"]
            st.info("Không tìm thấy sinh viên trong hệ thống.")
    except Exception as e:
        st.error(str(e))

# ===== FORM NHẬP LIỆU =====
st.markdown('<div class="student-detail-container">', unsafe_allow_html=True)

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    if str(st.session_state.get("f_year", "")) in years:
        academic_year = st.session_state["f_year"]
        st.text_input("Khóa", value=academic_year, disabled=True)
    else:
        academic_year = st.selectbox("Khóa", years, key="select_year")

with fc2:
    if st.session_state.get("f_major"):
        major_lbl = st.session_state["f_major"]
        st.text_input("Ngành", value=major_lbl, disabled=True)
    else:
        major_lbl = st.selectbox("Ngành", list(major_opts.values()), key="inp_major")

with fc3:
    if st.session_state.get("f_type"):
        type_lbl = st.session_state["f_type"]
        st.text_input("Loại", value=type_lbl, disabled=True)
    else:
        type_lbl = st.selectbox("Loại", list(type_opts.values()), key="inp_type")

with fc4:
    mssv = st.text_input("MSSV (*)", key="f_mssv")

# Row 2
r1c1, r1c2 = st.columns(2)
with r1c1:
    fullname = st.text_input("Họ tên (*):", key="inp_name")
with r1c2:
    phone = st.text_input("SĐT:", key="inp_phone")

# Row 3
r2c1, r2c2 = st.columns(2)
with r2c1:
    class_lbl = st.text_input("Lớp mặc định:", key="inp_class")
with r2c2:
    cccd = st.text_input("CCCD:", key="inp_cccd")

# Row 4
dob_val = st.session_state.get("inp_dob")
if not isinstance(dob_val, date):
    dob_val = date(2005, 1, 1)
dob = st.date_input("Ngày sinh:", value=dob_val, key="inp_dob")

st.markdown('</div>', unsafe_allow_html=True) # End Container

# ===== ACTIONS: ẢNH & LƯU =====
st.markdown("### Thao tác")
sb1, sb2, sb3 = st.columns(3)

with sb1:
    # Logic chuyển trang Capture
    if st.button("📸 Chụp ảnh sinh viên", key="s_capture", use_container_width=True):
        if not mssv:
            st.error("⚠ Vui lòng nhập MSSV trước khi chụp ảnh")
        elif not fullname:
            st.error("⚠ Vui lòng nhập tên sinh viên trước khi chụp ảnh")
        else:
            # 1. Lưu trang quay lại là add_student
            st.session_state["capture_prev_page"] = "pages/add_student.py"
            # 2. Lưu dữ liệu
            st.session_state["capture_mssv"] = mssv.strip()
            st.session_state["capture_name"] = fullname.strip()
            # 3. Chuyển trang
            st.switch_page("pages/capture_photo.py")

with sb2:
    # Save logic (Giữ nguyên logic của bạn)
    if st.button("💾 LƯU & GÁN VÀO LỚP", type="primary", use_container_width=True):
        if not mssv or not fullname:
            st.error("Thiếu thông tin bắt buộc!")
            st.stop()
        if not selected_class_id:
            st.error("Chưa chọn lớp!")
            st.stop()

        # Logic xử lý (Rút gọn cho dễ nhìn - Giữ nguyên logic cũ của bạn ở đây)
        is_existing = st.session_state.get("search_input") and st.session_state.get("f_mssv") == mssv
        
        if is_existing:
            found_id = st.session_state.get("found_student_id")
            if found_id:
                try:
                    assign_student_to_class(student_id=int(found_id), class_id=int(selected_class_id))
                    st.success(f"Đã gán sinh viên {fullname} vào lớp!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Lỗi gán: {e}")
            else:
                st.error("Lỗi mất ID sinh viên.")
        else:
            # Tạo mới
            major_id = next((int(k) for k, v in major_opts.items() if v == major_lbl), None)
            type_id = next((int(k) for k, v in type_opts.items() if v == type_lbl), None)
            payload = {
                "FullName": fullname, "StudentCode": mssv, "DefaultClass": class_lbl,
                "Phone": phone, "AcademicYear": academic_year, "DateOfBirth": dob.isoformat(),
                "CitizenID": cccd, "MajorID": major_id, "TypeID": type_id, "PhotoStatus": "NONE"
            }
            try:
                res = create_student(payload)
                # Giả sử res trả về dict có id
                new_id = res.get("StudentID") or res.get("id")
                if new_id:
                    assign_student_to_class(student_id=int(new_id), class_id=int(selected_class_id))
                    st.success(f"Đã tạo và gán sinh viên {fullname} vào lớp!")
                    st.balloons()
                    # Clear form
                    for k in ["inp_name", "f_mssv", "inp_phone"]: 
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

with sb3:
    st.button("Training data", key="s_train", use_container_width=True)