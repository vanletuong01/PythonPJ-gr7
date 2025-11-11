import streamlit as st
from pathlib import Path
from services.api_client import register_teacher

# Load CSS
css_path = Path(__file__).parent.parent / "public" / "css" / "register.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Cấu hình trang
st.set_page_config(
    page_title="Đăng ký - VAA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Layout: Left (Illustration) | Right (Form)
col1, col2 = st.columns([1, 1])

with col1:
    # Illustration
    illustration_path = Path(__file__).parent.parent / "public" / "images" / "illustration.png"
    if illustration_path.exists():
        st.image(str(illustration_path), use_column_width=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 100px 50px;">
                <h1 style="color: #667eea; font-size: 48px;"></h1>
                <h2 style="color: #333;">LOGIN ACCESS</h2>
                <p style="color: #888;">Secure registration portal</p>
            </div>
        """, unsafe_allow_html=True)

with col2:
    # Logo
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            st.image(str(logo_path), width=120)
    
    # Register title
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 class="register-title">Register</h1>
            <p class="register-subtitle">Please enter your details.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Register form
    with st.form("register_form"):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        name = st.text_input("Full Name", placeholder="Enter your name")

    submit = st.form_submit_button("Register")

    if submit:
        if not email or not password or not name:
            st.error("Please fill in all required fields")
        else:
            result = register_teacher(email=email, password=password, name=name, phone=phone)
            if result.get("success"):
                st.success("Đăng ký thành công! Đang chuyển hướng đến trang đăng nhập...")
                st.balloons()
                import time
                time.sleep(2)
                st.switch_page("pages/login.py")
            else:
                st.error(result.get("message", "Registration failed"))

    col_link1, col_link2, col_link3 = st.columns([1, 2, 1])
    with col_link2:
        st.markdown('<div style="text-align: center; margin-top: 20px; font-size: 13px; color: #666;">Have an account?</div>', unsafe_allow_html=True)
        if st.button("Login", key="go_to_login", use_container_width=True):
            st.switch_page("pages/login.py")
