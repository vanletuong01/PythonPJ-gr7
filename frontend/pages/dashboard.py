import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
import sys
from datetime import datetime, timedelta

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
from components.sidebar_dashboard import render_dashboard_sidebar
from services.api_client import get_students_in_class, get_attendance_by_date

# ==== PAGE CONFIG ====
st.set_page_config(page_title="Dashboard - VAA", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ==== LOAD CSS TỪ FILE NGOÀI ====
css_path = Path(__file__).parent.parent / "public" / "css" / "dashboard.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ==== CHECK LOGIN ====
if not st.session_state.get("logged_in", False):
    st.switch_page("pages/login.py")

# ==== CHECK CLASS ====
selected_class = st.session_state.get("selected_class_info")
if not selected_class:
    st.warning("⚠️ Vui lòng chọn lớp học trước.")
    st.stop()

# ==================================================================
# LOGIC REFRESH
# ==================================================================
if st.session_state.get("data_refresh_needed"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state["data_refresh_needed"] = False
    st.rerun()

render_dashboard_sidebar()

# ==================================================================
# 1. HEADER
# ==================================================================
st.markdown('<div class="simple-header">', unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 4, 2, 0.8], gap="small")

try: class_id = int(selected_class.get("ClassID"))
except: class_id = selected_class.get("ClassID")

with h4:
    if st.button("↻", key="btn_reload_dash", help="Tải lại dữ liệu"):
        st.cache_data.clear()
        st.rerun()

with h1: st.text_input("Mã lớp", value=selected_class.get("ClassName",""), disabled=True)
with h2: st.text_input("Tên môn", value=selected_class.get("FullClassName","") or selected_class.get("SubjectName",""), disabled=True)
with h3: st.text_input("Mã môn", value=selected_class.get("CourseCode",""), disabled=True)
st.markdown('</div><div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# ==================================================================
# 2. LẤY DỮ LIỆU
# ==================================================================
students = get_students_in_class(class_id) or []
attendance_hist = get_attendance_by_date(class_id) or []
total_students = len(students)

col_charts, col_list = st.columns([1.8, 1.2], gap="large")

# ==================================================================
# CỘT TRÁI: BIỂU ĐỒ (STYLE FIGMA)
# ==================================================================
with col_charts:
    st.markdown('<h3 style="color:#0a2540; font-size:20px; font-weight:700; margin-bottom:15px;">Sơ đồ chuyên cần của lớp</h3>', unsafe_allow_html=True)

    # 1. Xử lý ngày tháng
    def parse_date(d_str):
        if not d_str: return datetime.now()
        if isinstance(d_str, datetime): return d_str
        try: return pd.to_datetime(d_str)
        except: return datetime.now()

    start_date = parse_date(selected_class.get("StartDate"))
    end_date = parse_date(selected_class.get("EndDate"))
    
    # Định dạng hiển thị ngày
    fmt_start = start_date.strftime("%d/%m")
    fmt_end = end_date.strftime("%d/%m")

    # 2. Chuẩn bị dữ liệu cho biểu đồ
    chart_data = []

    # -- Cột mốc Bắt đầu (Luôn là 0) --
    chart_data.append({
        "Label": f"Bắt đầu\n({fmt_start})",
        "Value": 0,
        "Order": start_date.timestamp() - 1000, # Đảm bảo luôn nằm đầu
        "Color": "#e5e7eb"
    })

    # -- Dữ liệu điểm danh thực tế --
    if attendance_hist:
        for item in attendance_hist:
            d_obj = pd.to_datetime(item["date"])
            chart_data.append({
                "Label": d_obj.strftime("%d/%m"),
                "Value": item["present"],
                "Order": d_obj.timestamp(),
                "Color": "#3b82f6" # Màu xanh Figma
            })
    
    # -- Cột mốc Kết thúc (Luôn là 0) --
    chart_data.append({
        "Label": f"Kết thúc\n({fmt_end})",
        "Value": 0, 
        "Order": end_date.timestamp() + 1000, # Đảm bảo luôn nằm cuối
        "Color": "#e5e7eb"
    })

    df_chart = pd.DataFrame(chart_data)

    # 3. Cấu hình trục Y (Chiều cao cột)
    # Max là tổng sinh viên của lớp (hoặc 60 nếu chưa có SV để biểu đồ không bị bẹt)
    y_max = total_students if total_students > 0 else 60
    # Thêm chút khoảng trống phía trên (tăng 10%) để số trên đầu cột không bị cắt
    y_domain = [0, y_max * 1.1] 

    # 4. Vẽ biểu đồ với Altair
    # Base chart
    base = alt.Chart(df_chart).encode(
        x=alt.X('Label', 
                sort=alt.EncodingSortField(field="Order", order="ascending"),
                axis=alt.Axis(title=None, labelAngle=0, grid=False, labelColor="#666", tickSize=0)),
        y=alt.Y('Value', 
                scale=alt.Scale(domain=y_domain),
                axis=alt.Axis(title=None, grid=True, tickCount=4, gridColor="#f0f0f0", labelColor="#999"))
    )

    # Vẽ Cột (Bar)
    bars = base.mark_bar(
        width=40,
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        color=alt.Color('Color', scale=None), # Dùng màu định nghĩa trong data
        tooltip=['Label', 'Value']
    )

    # Vẽ Số lượng trên đầu cột (Text) - Giống số 55 trong Figma
    # Sửa: Tạo cột 'TextValue' chỉ hiện số nếu > 0
    df_chart["TextValue"] = df_chart["Value"].apply(lambda v: str(v) if v > 0 else "")

    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,  # Đẩy chữ lên trên cột 5px
        color="#3b82f6",
        fontWeight="bold"
    ).encode(
        text='TextValue'
    )

    # Kết hợp và Render
    final_chart = (bars + text).properties(height=320).configure_view(strokeOpacity=0)
    
    st.altair_chart(final_chart, use_container_width=True)

    if not attendance_hist:
        st.caption("ℹ️ Hiện tại chưa có dữ liệu điểm danh.")

# ==================================================================
# CỘT PHẢI: DANH SÁCH SINH VIÊN (Giữ nguyên như cũ)
# ==================================================================
with col_list:
    if students:
        def sort_key(s):
            name = s.get("StudentName") or s.get("FullName") or ""
            return name.split()[-1] if name else ""
        try:
            sorted_students = sorted(students, key=sort_key)
        except:
            sorted_students = students

        table_data = []
        for i, s in enumerate(sorted_students, 1):
            name = s.get("StudentName") or s.get("FullName") or "---"
            code = s.get("StudentCode") or s.get("student_code") or "---"
            table_data.append({"STT": i, "HỌ TÊN": name, "MSSV": code})

        # HTML Card Header
        st.markdown(f"""
        <div class="student-list-card">
            <div class="list-header">
                <span class="list-title">Danh sách lớp</span>
                <span class="badge-count">Sĩ số: {len(table_data)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render Table
        df_students = pd.DataFrame(table_data)
        st.table(df_students.set_index("STT"))
    else:
        st.markdown('<div class="student-list-card"><div class="empty-state">Danh sách trống</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("➕ Thêm sinh viên", use_container_width=True, type="primary", key="add_student_btn"):
        st.switch_page("pages/add_student.py")