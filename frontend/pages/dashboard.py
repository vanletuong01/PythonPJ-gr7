import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from components.header import render_header
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import get_classes, get_dashboard_stats, get_students_in_class, get_attendance_by_date
import pandas as pd
from datetime import datetime

selected_class_id = st.session_state.get("selected_class_id")
if selected_class_id is not None:
    classes = get_classes()
    class_info = next((c for c in classes if c.get("ClassID") == selected_class_id), None)
    if class_info:
        st.info(
            f"**Bạn đang xem dashboard của lớp:** {class_info.get('ClassName')} - {class_info.get('FullClassName')}"
        )
    else:
        st.warning("Không tìm thấy thông tin lớp đã chọn!")
else:
    st.warning("Bạn chưa chọn lớp. Vui lòng vào lớp từ trang 'Vào lớp'.")

st.set_page_config(
    page_title="Dashboard - VAA", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Load CSS cho header
header_css = Path(__file__).parent.parent / "public" / "css" / "header.css"
if header_css.exists():
    st.markdown(f"<style>{header_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Load CSS cho dashboard
dashboard_css = Path(__file__).parent.parent / "public" / "css" / "dashboard.css"
if dashboard_css.exists():
    st.markdown(f"<style>{dashboard_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== RENDER HEADER =====
class_info = None
filter_lop, filter_mon, filter_ma_mon = render_header(
    class_name=class_info.get("ClassName", "") if class_info else "",
    full_class_name=class_info.get("FullClassName", "") if class_info else "",
    course_code=class_info.get("CourseCode", "") if class_info else ""
)

render_dashboard_sidebar()

col_left, col_right = st.columns([2.5, 1.5])

with col_left:
    st.markdown("Sơ đồ chuyên cần của lớp")

    attendance_by_date = get_attendance_by_date(selected_class_id) if selected_class_id else []
    if attendance_by_date:
        df_att = pd.DataFrame(attendance_by_date)
        df_att["date"] = pd.to_datetime(df_att["date"])
        df_att = df_att.sort_values("date")
        df_att["Ngày học"] = df_att["date"].dt.strftime("%d/%m/%Y")
        st.bar_chart(df_att.set_index("Ngày học")["present"], height=250)
    else:
        st.info("Chưa có dữ liệu chuyên cần cho lớp này.")
with col_right:
    st.markdown("Danh sách sinh viên")

    if selected_class_id:
        students = get_students_in_class(selected_class_id)
        if students:
            # Sắp xếp theo tên
            students = sorted(students, key=lambda x: x["FullName"])
            df = pd.DataFrame([
                {
                    "STT": i + 1,
                    "HỌ TÊN": s["FullName"],
                    "MSSV": s["StudentCode"]
                } for i, s in enumerate(students)
            ])
            st.dataframe(df, use_container_width=True, hide_index=True, height=350)
            st.caption(f"**Sĩ số:** {len(students)}")
        else:
            st.warning("Lớp này chưa có sinh viên nào.")
    else:
        st.warning("Bạn chưa chọn lớp.")

    st.divider()
    if st.button("Thêm sinh viên", use_container_width=True, type="primary"):
        st.switch_page("pages/add_student.py")
