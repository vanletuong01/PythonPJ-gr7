import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime

# Thêm đường dẫn gốc để import module
sys.path.append(str(Path(__file__).parent.parent))

from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import get_classes, get_dashboard_stats, get_students_in_class, get_attendance_by_date

# --- CONFIG TRANG ---
st.set_page_config(
    page_title="Dashboard - VAA", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- XỬ LÝ DỮ LIỆU SESSION ---
selected_class_id = st.session_state.get("selected_class_id")
class_info = st.session_state.get("selected_class_info")

if not class_info and selected_class_id is not None:
    classes = get_classes()
    class_info = next((c for c in classes if c.get("ClassID") == selected_class_id), None)
    if class_info:
        st.info(
            f"**Bạn đang xem dashboard của lớp:** {class_info.get('ClassName')} - {class_info.get('FullClassName')}"
        )
    else:
        st.warning("Không tìm thấy thông tin lớp đã chọn!")
elif not class_info:
    st.warning("Bạn chưa chọn lớp. Vui lòng vào lớp từ trang 'Vào lớp'.")


# --- LOAD CSS (TÁCH BIỆT) ---
# Load CSS cho header
header_css = Path(__file__).parent.parent / "public" / "css" / "header.css"
if header_css.exists():
    st.markdown(f"<style>{header_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Load CSS cho dashboard (File bạn vừa tạo ở Bước 1)
dashboard_css = Path(__file__).parent.parent / "public" / "css" / "dashboard.css"
if dashboard_css.exists():
    st.markdown(f"<style>{dashboard_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


# --- RENDER GIAO DIỆN ---
filter_lop, filter_mon, filter_ma_mon = render_header(
    class_name=class_info.get("ClassName", "") if class_info else "",
    full_class_name=class_info.get("FullClassName", "") if class_info else "",
    course_code=class_info.get("CourseCode", "") if class_info else "",
    class_id=class_info.get("ClassID", "") if class_info else ""
)

render_dashboard_sidebar()

# --- CHIA CỘT DASHBOARD ---
col_left, col_right = st.columns([2.5, 1.5])

# === CỘT TRÁI: BIỂU ĐỒ ===
with col_left:
    st.markdown("### Sơ đồ chuyên cần của lớp")

    attendance_by_date = get_attendance_by_date(selected_class_id) if selected_class_id else []
    if attendance_by_date:
        df_att = pd.DataFrame(attendance_by_date)
        df_att["date"] = pd.to_datetime(df_att["date"])
        df_att = df_att.sort_values("date")
        df_att["Ngày học"] = df_att["date"].dt.strftime("%d/%m/%Y")
        st.bar_chart(df_att.set_index("Ngày học")["present"], height=350)
    else:
        st.info("Chưa có dữ liệu chuyên cần cho lớp này.")

# === CỘT PHẢI: DANH SÁCH SINH VIÊN (CODE MỚI) ===
with col_right:
    st.markdown("### Danh sách sinh viên")

    if selected_class_id:
        try:
            cid_int = int(selected_class_id)
        except:
            cid_int = None

        students = get_students_in_class(cid_int)

        if students:
            # Sắp xếp
            students = sorted(students, key=lambda x: x["FullName"])
            st.caption(f"Tổng số: **{len(students)}** sinh viên")
            
            # Header bảng
            h1, h2, h3 = st.columns([1.5, 6, 2.5])
            h1.markdown("**STT**")
            h2.markdown("**Họ tên / MSSV**")
            h3.markdown("**Thao tác**")
            st.divider()

            # Danh sách
            for i, s in enumerate(students):
                c1, c2, c3 = st.columns([1.5, 6, 2.5], vertical_alignment="center")
                
                c1.write(f"{i+1}")
                
                c2.markdown(
                    f"""
                    <div style="line-height: 1.4;">
                        <strong style="color: #333;">{s['FullName']}</strong><br>
                        <span style="color: #666; font-size: 0.9em;">MSSV: {s['StudentCode']}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                if c3.button("Chi tiết", key=f"btn_{s['StudentID']}", use_container_width=True):
                    st.session_state["selected_student_id"] = s["StudentID"]
                    st.switch_page("pages/student_detail.py")
                
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

        else:
            st.info("Lớp này chưa có sinh viên nào.")
    else:
        st.warning("Bạn chưa chọn lớp.")

    # Nút thêm mới
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Thêm sinh viên mới", use_container_width=True, type="primary"):
        st.switch_page("pages/add_student.py")
    if st.button("Quay lại trang dashboard", use_container_width=True, type="secondary"):
        st.switch_page("pages/dashboard.py")