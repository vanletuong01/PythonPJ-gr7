import streamlit as st
from pathlib import Path
from datetime import datetime
import sys

# ===== CẤU HÌNH =====
st.set_page_config(
    page_title="Chi tiết buổi học",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== IMPORT =====
sys.path.append(str(Path(__file__).parent.parent))
from services.api_client import get_session_detail, manual_checkin

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "attendance.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== KIỂM TRA SESSION =====
if not st.session_state.get("logged_in"):
    st.warning("Vui lòng đăng nhập!")
    st.stop()

selected_session = st.session_state.get("selected_session")
class_info = st.session_state.get("selected_class_info", {})

if not selected_session or not class_info:
    st.warning("Vui lòng chọn buổi học trước!")
    if st.button("← Quay lại chọn buổi"):
        st.switch_page("pages/select_session.py")
    st.stop()

# ===== HEADER =====
col_back, col_title = st.columns([0.5, 9.5])
with col_back:
    if st.button("←", key="btn_back", help="Quay lại chọn buổi"):
        st.switch_page("pages/select_session.py")

with col_title:
    st.markdown('<h3 style="margin:0; color:#0a2540;">CHI TIẾT BUỔI HỌC</h3>', unsafe_allow_html=True)

# ===== THÔNG TIN LỚP =====
c1, c2, c3 = st.columns(3)
with c1:
    st.text_input("Lớp:", value=class_info.get("ClassName", ""), disabled=True)
with c2:
    st.text_input("Môn:", value=class_info.get("FullClassName", ""), disabled=True)
with c3:
    st.text_input("Mã môn học:", value=class_info.get("CourseCode", ""), disabled=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===== THÔNG TIN BUỔI HỌC =====
session_number = selected_session['session_number']
session_date_display = selected_session['date']  # "17/11/2025"

# Chuyển format DD/MM/YYYY -> YYYY-MM-DD để gọi API
session_date_obj = selected_session['date_raw']
session_date_api = session_date_obj.strftime("%Y-%m-%d")

st.info(f"📅 **Buổi {session_number}** - {session_date_display}")

# ===== GỌI API LẤY DỮ LIỆU =====
data = get_session_detail(class_info.get("ClassID"), session_date_api)

if not data.get("success"):
    st.error(f"Lỗi: {data.get('message')}")
    st.stop()

total_students = data.get("total_students", 0)
total_attended = data.get("total_attended", 0)
total_absent = data.get("total_absent", 0)
attended_list = data.get("attended_list", [])
absent_list = data.get("absent_list", [])

# ===== THỐNG KÊ =====
st.markdown("### 📊 Thống kê buổi học")
stat_col1, stat_col2, stat_col3 = st.columns(3)

with stat_col1:
    st.metric("Tổng sinh viên", total_students)
with stat_col2:
    st.metric("Đã điểm danh", total_attended, delta=f"{(total_attended/total_students*100):.1f}%" if total_students > 0 else "0%")
with stat_col3:
    st.metric("Vắng", total_absent, delta=f"-{(total_absent/total_students*100):.1f}%" if total_students > 0 else "0%")

st.markdown("---")

# ===== DANH SÁCH SINH VIÊN =====
tab1, tab2 = st.tabs(["✅ Đã điểm danh", "❌ Chưa điểm danh"])

with tab1:
    if len(attended_list) == 0:
        st.info("Chưa có sinh viên nào điểm danh.")
    else:
        st.markdown(f"**Tổng: {len(attended_list)} sinh viên**")
        
        for idx, student in enumerate(attended_list, start=1):
            time_str = student.get("AttendanceTime", "--:--:--")
            
            # Kiểm tra đi trễ (giả sử tiết học bắt đầu 07:30:00)
            late_mark = ""
            if time_str and time_str != "--:--:--":
                try:
                    att_time = datetime.strptime(time_str, "%H:%M:%S").time()
                    class_start = datetime.strptime("07:30:00", "%H:%M:%S").time()
                    if att_time > class_start:
                        late_mark = "🔴 Trễ"
                except:
                    pass
            
            st.markdown(f"""
            <div style='background:#f0fdf4; border-left:4px solid #22c55e; padding:10px; margin-bottom:8px; border-radius:5px;'>
                <b>{idx}. {student['FullName']}</b> - {student['StudentCode']}<br>
                ⏰ Giờ điểm danh: <b>{time_str}</b> {late_mark}
            </div>
            """, unsafe_allow_html=True)

with tab2:
    if len(absent_list) == 0:
        st.success("Tất cả sinh viên đã điểm danh! 🎉")
    else:
        st.markdown(f"**Tổng: {len(absent_list)} sinh viên vắng**")
        
        # Khởi tạo state để lưu SV được chọn
        if "manual_checkin_students" not in st.session_state:
            st.session_state.manual_checkin_students = set()
        
        for idx, student in enumerate(absent_list, start=1):
            col_info, col_action = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"""
                <div style='background:#fef2f2; border-left:4px solid #ef4444; padding:10px; margin-bottom:8px; border-radius:5px;'>
                    <b>{idx}. {student['FullName']}</b> - {student['StudentCode']}
                </div>
                """, unsafe_allow_html=True)
            
            with col_action:
                # Checkbox để giáo viên chọn
                is_checked = st.checkbox(
                    "Điểm danh",
                    key=f"check_{student['StudyID']}",
                    value=student['StudyID'] in st.session_state.manual_checkin_students
                )
                
                if is_checked:
                    st.session_state.manual_checkin_students.add(student['StudyID'])
                else:
                    st.session_state.manual_checkin_students.discard(student['StudyID'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Nút LƯU ĐIỂM DANH THỦ CÔNG
        if len(st.session_state.manual_checkin_students) > 0:
            if st.button(f"💾 Lưu điểm danh cho {len(st.session_state.manual_checkin_students)} sinh viên", type="primary", use_container_width=True):
                success_count = 0
                fail_count = 0
                
                for study_id in st.session_state.manual_checkin_students:
                    result = manual_checkin(study_id, session_date_api)
                    if result.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                
                if fail_count == 0:
                    st.success(f"✅ Đã điểm danh thành công cho {success_count} sinh viên!")
                    st.session_state.manual_checkin_students.clear()
                    st.rerun()
                else:
                    st.warning(f"Thành công: {success_count}, Thất bại: {fail_count}")