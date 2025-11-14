import streamlit as st
from pathlib import Path
from services.api_client import login_teacher
import base64

st.set_page_config(
    page_title="Đăng nhập - VAA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
css_path = Path(__file__).parent.parent / "public" / "css" / "login.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    illustration_path = Path(__file__).parent.parent / "public" / "images" / "illustration.png"
    if illustration_path.exists():
        st.image(str(illustration_path), use_container_width=True)

with col2:
    # Logo 300px, căn giữa, xích phải 20px, lên trên
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(
            f'''<div class="login-logo-wrapper">
                  <img src="data:image/png;base64,{logo_b64}" class="login-logo" />
                </div>''',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="login-title-block" style="text-align:center;">
      <h1 style="margin:0;font-size:32px;color:#111;">Login</h1>
      <p style="color:#666;margin:6px 0 0;font-size:15px;">Welcome back!</p>
    </div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="••••••••")

    # Button login căn giữa
    col_empty1, col_btn, col_empty2 = st.columns([1, 2, 1])
    with col_btn:
        if st.button("Login", key="login_btn"):
            if not (email and password):
                st.error("❌ Vui lòng nhập email và mật khẩu")
            else:
                result = login_teacher(email, password)
                if result and result.get("success"):
                    st.success("✅ Đăng nhập thành công!")
                    st.session_state.logged_in = True
                    st.session_state.teacher = result.get("teacher", {})
                    st.switch_page("app.py")
                else:
                    st.error(f"❌ {result.get('message', 'Đăng nhập thất bại')}")

    # Register căn giữa
    st.markdown('<div style="text-align:center;margin-top:18px;font-size:14px;color:#777;">Don\'t have an account?</div>', unsafe_allow_html=True)
    
    col_reg1, col_reg2, col_reg3 = st.columns([1.5, 1, 1.5])
    with col_reg2:
        if st.button("Register", key="go_to_register"):
            st.switch_page("pages/register.py")
