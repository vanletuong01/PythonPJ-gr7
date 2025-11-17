import streamlit as st
from pathlib import Path

def render_dashboard_sidebar():
    """Sidebar cho dashboard sau khi login"""
    with st.sidebar:
        logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=200)
        
        st.markdown("### VIETNAM AVIATION ACADEMY")
        st.divider()
        
        # Thông tin giáo viên
        teacher = st.session_state.get("teacher", {})
        st.markdown(f"**{teacher.get('name', 'Giáo viên')}**")
        st.caption(f"{teacher.get('email', '')}")
        st.divider()
        
        # Menu navigation
        st.markdown("### Menu")
        
        if st.button("Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")
        
        if st.button("Thêm lớp học", use_container_width=True):
            st.switch_page("pages/add_class.py")
        
        if st.button("Thêm sinh viên", use_container_width=True):
            st.switch_page("pages/add_student.py")
        
        # ---- FIXED: Điểm danh ----
        if st.button("Điểm danh", use_container_width=True):
            st.switch_page("pages/diem_danh.py")   # Hoặc để st.info nếu chưa code
        
        st.divider()
        
        # Logout
        if st.button("Đăng xuất", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.switch_page("pages/login.py")
