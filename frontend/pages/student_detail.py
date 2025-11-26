import streamlit as st
from pathlib import Path
import sys

# ===== CONFIG TRANG =====
st.set_page_config(
    page_title="Hồ sơ sinh viên",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
from services.api_client import get_student_detail, get_student_attendance, remove_student_from_class, update_student_info
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "student_detail.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_dashboard_sidebar()

# ===== LẤY DỮ LIỆU =====
student_id = st.session_state.get("selected_student_id")
class_info = st.session_state.get("selected_class_info", {})

if not student_id:
    st.warning("Vui lòng chọn sinh viên từ Dashboard.")
    if st.button("Về Dashboard"):
        st.switch_page("pages/dashboard.py")
    st.stop()

# 1. Gọi API
student = get_student_detail(student_id)
if not student:
    st.error("Không tìm thấy thông tin sinh viên.")
    st.stop()

attendance_data = []
if class_info.get("ClassID"):
    attendance_data = get_student_attendance(class_info.get("ClassID"), student_id)

# ===== HEADER MÔN HỌC =====
render_header(
    class_name=class_info.get("ClassName", ""),
    full_class_name=class_info.get("FullClassName", ""),
    course_code=class_info.get("CourseCode", ""),
    class_id=class_info.get("ClassID", "")
)

# ===== NÚT BACK & TIÊU ĐỀ =====
col_nav, col_title = st.columns([0.05, 0.95])
with col_nav:
    if st.button("←", help="Quay lại Dashboard", use_container_width=True):
        st.switch_page("pages/dashboard.py")
with col_title:
    st.markdown(f"<div class='student-title'>Hồ sơ sinh viên</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Quản lý thông tin và điểm danh của {student.get('FullName')}</div>", unsafe_allow_html=True)

st.markdown("---")

# ===== FORM THÔNG TIN (Đã sửa lỗi khung trắng) =====
# Sử dụng container thuần của Streamlit để gom nhóm
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Họ và tên", value=student.get("FullName", ""), key="full_name")
        st.text_input("Lớp sinh hoạt", value=student.get("DefaultClass", ""), key="class")
        st.text_input("Ngày sinh (YYYY-MM-DD)", value=student.get("DateOfBirth", ""), key="birth_date")
    
    with c2:
        st.text_input("Mã số sinh viên", value=student.get("StudentCode", ""), disabled=True)
        st.text_input("Số điện thoại", value=student.get("Phone", ""), key="phone")
        st.text_input("CCCD/CMND", value=student.get("CitizenID", ""), key="cccd")
    
    st.text_input("Ngành học", value=student.get("Full_name_mj", ""), disabled=True)

# ===== ACTIONS (NÚT BẤM) =====
st.markdown("<br>", unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button("💾 LƯU THÔNG TIN", type="primary", use_container_width=True):
        ok = update_student_info(
            student_id=student_id,
            full_name=st.session_state["full_name"],
            default_class=st.session_state["class"],
            birth_date=st.session_state["birth_date"],
            phone=st.session_state["phone"],
            cccd=st.session_state["cccd"]
        )
        if ok:
            st.toast("✅ Đã lưu thông tin thành công!")
            st.rerun()
        else:
            st.error("Lưu thất bại.")

with b2:
    if st.button("🗑️ XÓA SINH VIÊN KHỎI LỚP", type="secondary", use_container_width=True):
        if class_info.get("ClassID"):
            if remove_student_from_class(class_info["ClassID"], student_id):
                st.success("Đã xóa thành công!")
                st.switch_page("pages/class_detail.py")
            else:
                st.error("Xóa thất bại.")

st.markdown("---")

# ===== ẢNH & TRAINING =====
col_img, col_train = st.columns([1, 1])
with col_img:
    has_photo = student.get("PhotoStatus", False)
    status_label = "<span class='status-tag-yes'>ĐÃ CÓ ẢNH</span>" if has_photo else "<span class='status-tag-no'>CHƯA CÓ ẢNH</span>"
    
    st.markdown(f"""
    <div class='status-box'>
        <span style='font-weight:600; color:#4a5568'>Dữ liệu khuôn mặt:</span>
        {status_label}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
    if st.button("📸 Cập nhật khuôn mặt", use_container_width=True):
        st.session_state["capture_prev_page"] = "pages/student_detail.py"
        st.session_state["capture_mssv"] = student.get("StudentCode", "")
        st.session_state["capture_name"] = student.get("FullName", "")
        st.switch_page("pages/capture_photo.py")

with col_train:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True) # Spacer
    st.info("Hệ thống sẽ tự động train lại sau khi cập nhật ảnh.")
    if st.button("⚡ Training thủ công (Nếu cần)", use_container_width=True):
        st.toast("Đang gửi lệnh training...", icon="⏳")

# ===== LỊCH SỬ ĐIỂM DANH =====
st.markdown("<div class='history-title'>Lịch sử điểm danh</div>", unsafe_allow_html=True)

if attendance_data:
    # Thống kê
    total = len(attendance_data)
    present = sum(1 for x in attendance_data if x.get('IsPresent'))
    rate = int((present/total)*100) if total > 0 else 0
    
    c_s1, c_s2, c_s3 = st.columns(3)
    c_s1.metric("Tổng buổi", total)
    c_s2.metric("Có mặt", present)
    c_s3.metric("Tỷ lệ chuyên cần", f"{rate}%", delta_color="normal")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render List
    for item in attendance_data:
        buoi = item.get("SessionNumber", "?")
        ngay = item.get("Date", "")
        is_present = item.get("IsPresent", False)
        gio = item.get("Time", "--:--")
        
        css_cls = "att-present" if is_present else "att-absent"
        status_txt = "<span class='status-ok'>✅ Có mặt</span>" if is_present else "<span class='status-miss'>❌ Vắng</span>"
        time_display = gio if is_present else ""

        st.markdown(f"""
        <div class='att-item {css_cls}'>
            <div class='att-info'>
                <span class='att-session'>Buổi {buoi}</span>
                <span class='att-date'>{ngay}</span>
            </div>
            <div class='att-status'>{status_txt}</div>
            <div class='att-time'>{time_display}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Chưa có dữ liệu điểm danh nào.")