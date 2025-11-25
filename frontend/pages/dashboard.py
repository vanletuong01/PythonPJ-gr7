import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
import sys
import io
from datetime import datetime

# ===== IMPORT SERVICES =====
sys.path.append(str(Path(__file__).parent.parent))
from components.sidebar_dashboard import render_dashboard_sidebar
# Nhớ import hàm get_export_data mới thêm
from services.api_client import get_students_in_class, get_attendance_by_date, get_export_data

# ==== PAGE CONFIG ====
st.set_page_config(page_title="Dashboard - VAA", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ==== LOAD CSS ====
css_path = Path(__file__).parent.parent / "public" / "css" / "dashboard.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ==== CHECK LOGIN ====
if not st.session_state.get("logged_in", False):
    st.switch_page("pages/login.py")

selected_class = st.session_state.get("selected_class_info")
if not selected_class:
    st.warning("⚠️ Vui lòng chọn lớp học trước.")
    st.stop()

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
# CỘT TRÁI: BIỂU ĐỒ
# ==================================================================
with col_charts:
    st.markdown('<h3 style="color:#0a2540; font-size:20px; font-weight:700; margin-bottom:15px;">Sơ đồ chuyên cần của lớp</h3>', unsafe_allow_html=True)

    def parse_date(d_str):
        if not d_str: return datetime.now()
        if isinstance(d_str, datetime): return d_str
        try: return pd.to_datetime(d_str)
        except: return datetime.now()

    start_date = parse_date(selected_class.get("StartDate"))
    end_date = parse_date(selected_class.get("EndDate"))
    
    chart_data = []
    chart_data.append({
        "Label": f"Bắt đầu\n({start_date.strftime('%d/%m')})",
        "Value": 0, "Order": start_date.timestamp() - 1000, "Color": "#e5e7eb"
    })

    if attendance_hist:
        for item in attendance_hist:
            d_obj = pd.to_datetime(item["date"])
            chart_data.append({
                "Label": d_obj.strftime("%d/%m"),
                "Value": item["present"],
                "Order": d_obj.timestamp(),
                "Color": "#3b82f6"
            })
    
    chart_data.append({
        "Label": f"Kết thúc\n({end_date.strftime('%d/%m')})",
        "Value": 0, "Order": end_date.timestamp() + 1000, "Color": "#e5e7eb"
    })

    df_chart = pd.DataFrame(chart_data)
    y_max = total_students if total_students > 0 else 60
    
    base = alt.Chart(df_chart).encode(
        x=alt.X('Label', sort=alt.EncodingSortField(field="Order", order="ascending"), axis=alt.Axis(title=None, labelAngle=0, grid=False)),
        y=alt.Y('Value', scale=alt.Scale(domain=[0, y_max * 1.1]), axis=alt.Axis(title=None, grid=True))
    )

    bars = base.mark_bar(width=40, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        color=alt.Color('Color', scale=None),
        tooltip=['Label', 'Value']
    )
    
    df_chart["TextValue"] = df_chart["Value"].apply(lambda v: str(v) if v > 0 else "")
    text = base.mark_text(align='center', baseline='bottom', dy=-5, color="#3b82f6", fontWeight="bold").encode(text='TextValue')

    st.altair_chart((bars + text).properties(height=320).configure_view(strokeOpacity=0), use_container_width=True)
    if not attendance_hist: st.caption("ℹ️ Hiện tại chưa có dữ liệu điểm danh.")

# ==================================================================
# CỘT PHẢI: DANH SÁCH & EXPORT EXCEL
# ==================================================================
with col_list:
    # --- PHẦN DANH SÁCH SINH VIÊN ---
    if students:
        def sort_key(s):
            name = s.get("StudentName") or s.get("FullName") or ""
            return name.split()[-1] if name else ""
        try: sorted_students = sorted(students, key=sort_key)
        except: sorted_students = students

        table_data = []
        for i, s in enumerate(sorted_students, 1):
            name = s.get("StudentName") or s.get("FullName") or "---"
            code = s.get("StudentCode") or s.get("student_code") or "---"
            table_data.append({"STT": i, "HỌ TÊN": name, "MSSV": code})

        st.markdown(f"""
        <div class="student-list-card">
            <div class="list-header">
                <span class="list-title">Danh sách lớp</span>
                <span class="badge-count">Sĩ số: {len(table_data)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        df_students = pd.DataFrame(table_data)
        for idx, row in df_students.iterrows():
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;padding:4px 0;'>"
                f"<span style='width:32px;display:inline-block;'>{row['STT']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            btn_label = f"{row['HỌ TÊN']} ({row['MSSV']})"
            
            if st.button(btn_label, key=f"btn_view_{row['MSSV']}", use_container_width=True):
                selected_student = sorted_students[idx] 
                st.session_state["selected_student_id"] = selected_student.get("StudentID") or selected_student.get("id")
                st.switch_page("pages/student_detail.py")
    else:
        st.markdown('<div class="student-list-card"><div class="empty-state">Danh sách trống</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

    # --- NÚT EXPORT EXCEL ---
    # Logic: Bấm nút để lấy dữ liệu -> Convert sang Excel -> Hiện nút Download
    
    # 1. Hàm convert DataFrame sang Excel Bytes
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='DiemDanh')
        processed_data = output.getvalue()
        return processed_data

    # 2. Giao diện nút
    col_export, col_add = st.columns([1, 1])
    
    with col_export:
        # Sử dụng popover (menu nhỏ) hoặc xử lý trực tiếp
        # Ở đây mình xử lý trực tiếp: Gọi API lấy dữ liệu thô
        export_raw = get_export_data(class_id)
        
        if export_raw:
            df_export = pd.DataFrame(export_raw)
            # Sắp xếp cho đẹp: Ngày -> Tên
            if not df_export.empty:
                excel_data = to_excel(df_export)
                file_name = f"DiemDanh_{selected_class.get('ClassName')}_{datetime.now().strftime('%d%m%Y')}.xlsx"
                
                st.download_button(
                    label="📥 Xuất Excel",
                    data=excel_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="secondary"
                )
        else:
            st.button("📥 Xuất Excel", disabled=True, use_container_width=True, help="Không có dữ liệu để xuất")

    with col_add:
        if st.button("➕ Thêm SV", use_container_width=True, type="primary", key="add_student_btn"):
            st.switch_page("pages/add_student.py")