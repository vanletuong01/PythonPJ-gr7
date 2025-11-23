import streamlit as st
from pathlib import Path
import sys

# ===== CONFIG TRANG =====
st.set_page_config(
    page_title="Chi tiết sinh viên",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
from services.api_client import get_student_detail, get_student_attendance
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "student_detail.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_dashboard_sidebar()

# ===== LẤY DỮ LIỆU SESSION =====
student_id = st.session_state.get("selected_student_id")
class_info = st.session_state.get("selected_class_info", {})

if not student_id:
    st.warning("Vui lòng chọn sinh viên từ Dashboard.")
    if st.button("Về Dashboard"):
        st.switch_page("pages/dashboard.py")
    st.stop()

# 1. Gọi API lấy chi tiết sinh viên
student = get_student_detail(student_id)
if not student:
    st.error("Không tìm thấy thông tin sinh viên.")
    st.stop()

# 2. Gọi API lấy điểm danh
attendance_data = []
if class_info.get("ClassID"):
    attendance_data = get_student_attendance(class_info.get("ClassID"), student_id)

# ===== HEADER =====
render_header(
    class_name=class_info.get("ClassName", ""),
    full_class_name=class_info.get("FullClassName", ""),
    course_code=class_info.get("CourseCode", ""),
    class_id=class_info.get("ClassID", "")
)

# [ĐÃ XÓA] Phần nút Quay lại Dashboard lớn tại đây

# ===== TIÊU ĐỀ: NÚT BACK + TIÊU ĐỀ (cùng 1 hàng) =====
col_back, col_title = st.columns([0.05, 0.95])
with col_back:
    if st.button("←", use_container_width=True):
        st.switch_page("pages/dashboard.py")
with col_title:
    st.markdown(
        "<div class='student-detail-title' style='margin-bottom:0;'>Hồ sơ sinh viên</div>",
        unsafe_allow_html=True
    )

# ===== FORM THÔNG TIN =====
# [ĐÃ XÓA] Dòng div student-detail-container gây ra khoảng trắng thừa
# st.markdown("<div class='student-detail-container'>", unsafe_allow_html=True)

st.markdown("<div class='student-detail-form'>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.text_input("Họ tên:", value=student.get("FullName", ""), key="full_name")
    st.text_input("Lớp mặc định:", value=student.get("DefaultClass", ""), key="class")
    st.text_input("Ngày sinh:", value=student.get("DateOfBirth", ""), key="birth_date")
with c2:
    st.text_input("MSSV:", value=student.get("StudentCode", ""), disabled=True)
    st.text_input("Số điện thoại:", value=student.get("Phone", ""), key="phone")
    st.text_input("CCCD/CMND:", value=student.get("CitizenID", ""), key="cccd")

st.text_input("Ngành học:", value=student.get("Full_name_mj", ""), disabled=True)
st.markdown("</div>", unsafe_allow_html=True)

# ===== NÚT SAVE/DELETE =====
st.markdown("<br>", unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    st.button("LƯU THÔNG TIN (SAVE)", type="primary", use_container_width=True)
with b2:
    st.button("XÓA SINH VIÊN (DELETE)", type="secondary", use_container_width=True)

st.divider()

# ===== TRẠNG THÁI ẢNH & CHUYỂN TRANG CAPTURE =====
col_img, col_train = st.columns([1, 1])
with col_img:
    has_photo = student.get("PhotoStatus", False)
    status_html = "<span class='status-yes'>ĐÃ CÓ ẢNH</span>" if has_photo else "<span class='status-no'>CHƯA CÓ ẢNH</span>"
    
    st.markdown(f"""
        <div class='status-row'>
            <span class='status-label'>Trạng thái ảnh:</span>
            {status_html}
        </div>
    """, unsafe_allow_html=True)
    
    # --- LOGIC CHUYỂN TRANG CHỤP ẢNH ---
    if st.button("📸 Lấy ảnh / Chụp ảnh", use_container_width=True):
        # 1. Lưu trang hiện tại để quay lại
        st.session_state["capture_prev_page"] = "pages/student_detail.py"
        
        # 2. Lưu thông tin sinh viên để hiển thị bên kia
        st.session_state["capture_mssv"] = student.get("StudentCode", "")
        st.session_state["capture_name"] = student.get("FullName", "")
        
        # 3. Chuyển trang
        st.switch_page("pages/capture_photo.py")

with col_train:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ Training Data", use_container_width=True):
        st.toast("Đang gửi yêu cầu training...", icon="⏳")

# ===== LỊCH SỬ ĐIỂM DANH =====
st.markdown("<div style='margin-top:30px' class='student-detail-title'>Lịch sử điểm danh</div>", unsafe_allow_html=True)
st.markdown("<div class='attendance-list'>", unsafe_allow_html=True)

if attendance_data:
    for item in attendance_data:
        buoi = item.get("SessionNumber", "?")
        ngay = item.get("Date", "")
        is_present = item.get("IsPresent", False)
        gio = item.get("Time", "--:--") if is_present else "--:--"
        
        status_text = "Đã điểm danh" if is_present else "Vắng"
        status_class = "" if is_present else "miss"

        st.markdown(
            f"""
            <div class='attendance-item'>
                <span class='buoi'>Buổi {buoi}</span>
                <span class='date'>{ngay}</span>
                <span class='status {status_class}'>{status_text}</span>
                <span class='time'>{gio}</span>
            </div>
            """, unsafe_allow_html=True
        )
else:
    st.info(f"Chưa có dữ liệu điểm danh cho lớp {class_info.get('ClassName', 'này')}.")

st.markdown("</div>", unsafe_allow_html=True)
# [ĐÃ XÓA] div đóng của container
# st.markdown("</div>", unsafe_allow_html=True)