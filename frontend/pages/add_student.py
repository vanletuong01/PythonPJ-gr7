import streamlit as st
from datetime import date, datetime
from pathlib import Path
import sys
import time

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import (
    create_student, search_students, get_classes,
    get_majors, get_types, assign_student_to_class
)

st.set_page_config(page_title="Thêm Sinh Viên", layout="wide")

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "add-student.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_dashboard_sidebar()

# ===== PREPARE DATA =====
majors = get_majors() or []
classes = get_classes() or []
types = get_types() or []

def to_opts(items, idk, namek):
    return {str(i[idk]): i[namek] for i in items if isinstance(i, dict) and i.get(idk)}

major_opts = to_opts(majors, "MajorID", "MajorName")
type_opts = to_opts(types, "TypeID", "TypeName")

current_year = datetime.now().year
years = [str(y) for y in range(2000, current_year + 1)]

# ===== LẤY THÔNG TIN TỪ DASHBOARD =====
selected_class_id = st.session_state.get("selected_class_id")
class_info = {}

if selected_class_id:
    # Tìm thông tin lớp dựa trên ID
    found_class = next((c for c in classes if str(c.get("ClassID")) == str(selected_class_id)), None)
    if found_class:
        class_info = found_class

# ================= UI PART 1 =================
c_info1, c_info2, c_info3 = st.columns(3)
with c_info1:
    st.text_input("Lớp:", value=class_info.get("ClassName", ""), disabled=True)
with c_info2:
    st.text_input("Môn:", value=class_info.get("FullClassName", "") or class_info.get("SubjectName", ""), disabled=True)
with c_info3:
    st.text_input("Mã môn học:", value=class_info.get("CourseCode", ""), disabled=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ================= UI PART 2: HEADER =================
h_col1, h_col2 = st.columns([0.5, 9.5])
with h_col1:
    if st.button("←", key="btn_back_arrow", help="Quay lại Dashboard"):
        # Trước khi quay lại, bật cờ reload để chắc chắn
        st.session_state["data_refresh_needed"] = True
        st.switch_page("pages/dashboard.py")
with h_col2:
    st.markdown('<h3 class="page-header-title">THÊM SINH VIÊN MỚI</h3>', unsafe_allow_html=True)

# ================= UI PART 3: SEARCH =================
st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
s_col1, s_col2 = st.columns([4, 1], gap="medium")

with s_col1:
    st.markdown('<div style="height: 29px;"></div>', unsafe_allow_html=True)
    search_q = st.text_input("search_main", placeholder="Nhập MSSV hoặc Tên...", label_visibility="collapsed")

with s_col2:
    st.markdown('<div style="height: 29px;"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="btn-add-class">', unsafe_allow_html=True)
        btn_add_existing = st.button("Thêm vào lớp", key="btn_add_to_class")
        st.markdown('</div>', unsafe_allow_html=True)

# --- LOGIC TÌM KIẾM ---
search_status = None 
if search_q and len(search_q.strip()) >= 2:
    try:
        res = search_students(search_q.strip())
        rows = res.get("data", []) if isinstance(res, dict) else res
        
        if rows:
            found_student = rows[0]
            search_status = "found"
            st.session_state["found_student_id_for_add"] = found_student.get("StudentID")
            
            # Auto-fill form
            st.session_state["inp_mssv_final"] = found_student.get("StudentCode") or ""
            st.session_state["inp_name_final"] = found_student.get("FullName") or ""
            st.session_state["inp_phone_final"] = found_student.get("Phone") or ""
            st.session_state["inp_class_final"] = str(found_student.get("DefaultClass") or "")
            st.session_state["inp_cccd_final"] = found_student.get("CitizenID") or ""
            st.session_state["inp_year"] = str(found_student.get("AcademicYear") or "2000")
            
            mid = str(found_student.get("MajorID"))
            tid = str(found_student.get("TypeID"))
            if mid in major_opts: st.session_state["sel_major_idx"] = list(major_opts.keys()).index(mid)
            if tid in type_opts: st.session_state["sel_type_idx"] = list(type_opts.keys()).index(tid)
        else:
            search_status = "not_found"
    except Exception as e:
        st.error(f"Lỗi tìm kiếm: {e}")

if search_status == "not_found": st.warning(f"⚠️ Không tìm thấy '{search_q}'")
elif search_status == "found": st.success("✅ Đã tìm thấy sinh viên!")

# --- LOGIC THÊM VÀO LỚP (EXISTING) ---
if btn_add_existing:
    sid = st.session_state.get("found_student_id_for_add")
    if sid and selected_class_id:
        try:
            # ÉP KIỂU INT ĐỂ TRÁNH LỖI DATA
            assign_student_to_class(student_id=int(sid), class_id=int(selected_class_id))
            
            # [CỰC KỲ QUAN TRỌNG] Xóa sạch cache và đặt cờ
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state["data_refresh_needed"] = True
            
            st.toast(f"🎉 Đã thêm thành công!", icon="✅")
            time.sleep(0.5) # Đợi xíu cho DB kịp lưu
            st.rerun() # Load lại để form sạch sẽ
        except Exception as e:
            st.error(f"Lỗi: {e}")
    else:
        st.error("⚠️ Vui lòng tìm sinh viên và chọn lớp trước.")

# ================= UI PART 4: FORM NHẬP MỚI =================
st.markdown('<div class="student-detail-container">', unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns(4)
with f1:
    idx_y = years.index(st.session_state.get("inp_year")) if st.session_state.get("inp_year") in years else 0
    academic_year = st.selectbox("Khóa", years, index=idx_y, key="inp_year_box") 
with f2:
    idx_m = st.session_state.get("sel_major_idx", 0)
    major_id_sel = st.selectbox("Ngành", list(major_opts.keys()), format_func=lambda x: major_opts[x], index=idx_m, key="inp_major")
with f3:
    idx_t = st.session_state.get("sel_type_idx", 0)
    type_id_sel = st.selectbox("Loại", list(type_opts.keys()), format_func=lambda x: type_opts[x], index=idx_t, key="inp_type")
with f4:
    mssv = st.text_input("MSSV (*)", key="inp_mssv_final")

r1c1, r1c2 = st.columns(2)
with r1c1: fullname = st.text_input("Họ tên (*):", key="inp_name_final")
with r1c2: phone = st.text_input("SĐT (*):", key="inp_phone_final")

r2c1, r2c2 = st.columns(2)
with r2c1: class_lbl = st.text_input("Lớp mặc định (*):", key="inp_class_final")
with r2c2: cccd = st.text_input("CCCD (*):", key="inp_cccd_final")

dob = st.date_input("Ngày sinh (*):", value=date(2005, 1, 1), key="inp_dob")
st.markdown('</div><br>', unsafe_allow_html=True)

# ================= ACTIONS =================
b1, b2, b3 = st.columns(3)
with b1: st.button("Training data", use_container_width=True)
with b2:
    if st.button("📸 Lấy ảnh sinh viên", use_container_width=True):
        if mssv and fullname:
            st.session_state.update({"capture_prev_page": "pages/add_student.py", "capture_mssv": mssv, "capture_name": fullname})
            st.switch_page("pages/capture_photo.py")
        else:
            st.warning("⚠ Nhập MSSV & Tên trước")

with b3:
    if st.button("💾 LƯU MỚI", type="primary", use_container_width=True):
        if not mssv or not fullname or not selected_class_id:
            st.error("Thiếu thông tin bắt buộc (MSSV, Tên, Lớp).")
        else:
            try:
                payload = {
                    "FullName": fullname, "StudentCode": mssv, "DefaultClass": class_lbl,
                    "Phone": phone, "AcademicYear": academic_year, "DateOfBirth": dob.isoformat(),
                    "CitizenID": cccd, "MajorID": int(major_id_sel) if major_id_sel else None,
                    "TypeID": int(type_id_sel) if type_id_sel else None, "PhotoStatus": "NONE"
                }
                st.write("DEBUG payload:", payload)  # Thêm dòng này để kiểm tra dữ liệu gửi đi
                res = create_student(payload)
                st.write("DEBUG response:", res)     # Thêm dòng này để kiểm tra phản hồi

                new_id = res.get("StudentID") or res.get("id") or res.get("student_id")
                if not new_id and "detail" in res:
                    st.warning(f"Lỗi backend: {res['detail']}")
                elif new_id:
                    assign_student_to_class(student_id=int(new_id), class_id=int(selected_class_id))
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.session_state["data_refresh_needed"] = True
                    st.toast(f"✅ Thêm {fullname} thành công!", icon="🎉")
                    for k in ["inp_mssv_final", "inp_name_final", "inp_phone_final", "inp_class_final", "inp_cccd_final"]:
                        if k in st.session_state: del st.session_state[k]
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Không tạo được (có thể trùng MSSV hoặc thiếu trường bắt buộc).")
            except Exception as e:
                st.error(f"Lỗi: {e}")