import streamlit as st
from pathlib import Path
from services.api_client import login_teacher

# Cấu hình trang
st.set_page_config(
    page_title="Đăng nhập - VAA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

login_css_path = Path(__file__).parent.parent / "public" / "css" / "login.css"
if login_css_path.exists():
    with open(login_css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])

with col1:
    # Illustration
    illustration_path = Path(__file__).parent.parent / "public" / "images" / "illustration.png"
    if illustration_path.exists():
        st.image(str(illustration_path), use_container_width=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 100px 50px;">
                <h1 style="color: #667eea; font-size: 48px;"></h1>
                <h2 style="color: #333;">LOGIN ACCESS</h2>
                <p style="color: #888;">Secure login portal</p>
            </div>
        """, unsafe_allow_html=True)

with col2:
    # Logo
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            st.image(str(logo_path), width=120)
    
    # Welcome text
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 class="welcome-title">Welcome back</h1>
            <p class="welcome-subtitle">Welcome back! Please enter your details.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Log in")
    if submit:
        if not email or not password:
            st.error("Vui lòng điền đầy đủ thông tin.")
        else:
            result = login_teacher(email, password)
            if result.get("success"):
                st.session_state.logged_in = True
                st.session_state.teacher = result["user"]  # Lưu thông tin giáo viên vào session
                st.success("Đăng nhập thành công!")
                st.balloons()
                st.switch_page("app.py")
            else:
                st.error(result.get("message", "Đăng nhập thất bại"))
    
    col_link1, col_link2, col_link3 = st.columns([1, 2, 1])
    with col_link2:
        st.markdown('<div style="text-align: center; margin-top: 20px; font-size: 13px; color: #666;">Don\'t have an account?</div>', unsafe_allow_html=True)
        if st.button("Register", key="go_to_register", use_container_width=True):
            st.switch_page("pages/register.py")
