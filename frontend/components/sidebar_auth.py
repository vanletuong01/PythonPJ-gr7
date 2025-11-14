import streamlit as st
from pathlib import Path

def render_auth_sidebar():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            min-width: 350px !important;
            max-width: 350px !important;
            background: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        .sidebar-logo img {
            width: 300px !important;
            height: auto !important;
            display: block;
            margin: 0 auto 18px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        }
        .dual-buttons .stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path))

        st.markdown("""
        <div style="text-align:center;padding:12px 8px;">
            <h3 style="margin:6px 0;font-size:17px;letter-spacing:1.2px;color:#666;text-transform:uppercase;">Vietnam Aviation Academy</h3>
            <h2 style="margin:8px 0;font-size:22px;font-weight:600;color:#222;">Học Viện Hàng Không Việt Nam</h2>
            <p style="font-size:15px;color:#888;margin-top:8px;">Chào mừng tới trang điểm danh sinh viên</p>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("logged_in", False):
            st.markdown("---")
            st.markdown("**Đăng nhập / Đăng ký**")
            col_login, col_register = st.columns(2, gap="small")
            with col_login:
                login_clicked = st.button("🔐 Đăng nhập", key="login_btn")
            with col_register:
                register_clicked = st.button("📝 Đăng ký", key="register_btn")
            if login_clicked:
                st.switch_page("pages/login.py")
            if register_clicked:
                st.switch_page("pages/register.py")
        else:
            teacher_name = st.session_state.get("teacher", {}).get("name", "User")
            st.success(f"👤 Xin chào, {teacher_name}!")
            if st.button("🚪 Đăng xuất"):
                st.session_state.logged_in = False
                st.session_state.teacher = {}
                st.rerun()
