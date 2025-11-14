import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from components.header import render_header
from services.api_client import get_classes, get_dashboard_stats
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Dashboard - VAA", 
    layout="wide", 
    page_icon="📊",
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
filter_lop, filter_mon, filter_ma_mon = render_header()

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### Dashboard")
    st.divider()
    
    avatar_path = Path(__file__).parent.parent / "public" / "images" / "avatar.png"
    if avatar_path.exists():
        col_avatar, col_info = st.columns([1, 2])
        with col_avatar:
            st.image(str(avatar_path), width=60)
        with col_info:
            teacher_name = st.session_state.get("teacher", {}).get("name", "Giáo viên")
            st.markdown(f"**{teacher_name}**")
            st.caption("👨‍🏫 Giảng viên")
    
    st.divider()
    st.markdown("**Điểm Danh**")
    st.divider()
    
    current_time = datetime.now().strftime("%H:%M:%S T%u,%d/%m/%Y")
    st.markdown(f"**🕐 {current_time}**")
    
    st.divider()
    
    if st.button("OUT", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.switch_page("app.py")

# ===== MAIN CONTENT =====
col_left, col_right = st.columns([2.5, 1.5])

with col_left:
    st.markdown("### 📊 Sơ đồ chuyên cần của lớp")
    
    stats = get_dashboard_stats()
    attendance_data = stats.get("attendance_by_month", [])
    
    if attendance_data:
        df_attendance = pd.DataFrame(attendance_data)
        df_attendance.columns = ["Tháng", "Số lượng"]
        st.bar_chart(df_attendance.set_index("Tháng"), height=250)
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("📚 Tổng số lớp", stats.get('total_classes', 0))
        with col_stat2:
            st.metric("👥 Tổng sinh viên", stats.get('total_students', 0))
    else:
        mock_data = pd.DataFrame({
            "Tháng": ["Ngày bắt đầu", "Nov 2021", "Dec 2021", "Jan 2022", "Ngày kết thúc"],
            "Số lượng": [0, 0, 55, 0, 0]
        })
        st.bar_chart(mock_data.set_index("Tháng"), height=250)
    
    st.divider()
    
    st.markdown("### 📉 Sơ đồ sinh viên vắng mặt trên 1 buổi")
    absent_data = pd.DataFrame({
        "Loại": ["Mssv", "Mssv"],
        "Số lượng": [2, 1]
    })
    st.bar_chart(absent_data.set_index("Loại"), height=200)

with col_right:
    st.markdown("### 📋 Danh sách lớp")
    
    filter_siso = st.text_input("Sĩ số:", placeholder="VD: 30", label_visibility="collapsed")
    st.caption("**Sĩ số:**")
    
    classes = get_classes()
    
    if classes:
        filtered_classes = classes
        if filter_lop:
            filtered_classes = [c for c in filtered_classes if filter_lop.lower() in str(c.get("ClassName", "")).lower()]
        if filter_mon:
            filtered_classes = [c for c in filtered_classes if filter_mon.lower() in str(c.get("Session", "")).lower()]
        if filter_ma_mon:
            filtered_classes = [c for c in filtered_classes if filter_ma_mon.lower() in str(c.get("FullClassName", "")).lower()]
        
        if filtered_classes:
            df = pd.DataFrame([
                {
                    "STT": i+1,
                    "HỌ TÊN": c.get("Teacher_class", "N/A"),
                    "MSSV": str(c.get("ClassID", ""))[:10]
                } for i, c in enumerate(filtered_classes[:20])
            ])
            st.dataframe(df, use_container_width=True, hide_index=True, height=350)
        else:
            st.warning("⚠️ Không tìm thấy lớp nào")
    else:
        mock_df = pd.DataFrame([
            {"STT": 1, "HỌ TÊN": "Nguyễn Văn A", "MSSV": "2331540061"},
            {"STT": 2, "HỌ TÊN": "Nguyễn Văn A", "MSSV": "2331540061"},
            {"STT": 3, "HỌ TÊN": "Nguyễn Văn A", "MSSV": "2331540061"},
            {"STT": 4, "HỌ TÊN": "Nguyễn Văn A", "MSSV": "2331540061"},
        ])
        st.dataframe(mock_df, use_container_width=True, hide_index=True, height=350)
    
    st.divider()
    
    if st.button("Thêm sinh viên", use_container_width=True, type="primary"):
        st.info("🔜 Chức năng đang phát triển")