import streamlit as st
from pathlib import Path
from services.api_client import register_teacher
import base64

st.set_page_config(
    page_title="Đăng ký - VAA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
css_path = Path(__file__).parent.parent / "public" / "css" / "register.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    illustration_path = Path(__file__).parent.parent / "public" / "images" / "illustration.png"
    if illustration_path.exists():
        st.image(str(illustration_path), use_container_width=True)

with col2:
    # Logo
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(
            f'''<div class="register-logo-wrapper">
                  <img src="data:image/png;base64,{logo_b64}" class="register-logo" />
                </div>''',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="register-title-block" style="text-align:center;">
      <h1 style="margin:0;font-size:32px;color:#111;">Register</h1>
      <p style="color:#666;margin:8px 0 0;font-size:15px;">Please enter your details.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        email = st.text_input("Email", placeholder="Enter your email")
        
        # type="password" sẽ tự có mắt, CSS bên dưới sẽ làm cho nó hoạt động
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        name = st.text_input("Full Name", placeholder="Enter your name")
        
        # Nút Register
        submit = st.form_submit_button("Register", use_container_width=True)

        if submit:
            if not (email and password and name):
                st.error("❌ Vui lòng điền đầy đủ thông tin")
            else:
                res = register_teacher(email=email, password=password, name=name)
                if res.get("status") in (200, 201) or res.get("id_login"):
                    st.success("✅ Đăng ký thành công!")
                    st.balloons()
                    st.switch_page("pages/login.py")
                else:
                    msg = res.get("message") or res.get("detail") or "Lỗi không xác định"
                    st.error(f"❌ Đăng ký thất bại: {msg}")

    st.markdown('<div style="text-align:center;margin-top:20px;font-size:14px;color:#777;">Already have an account?</div>', unsafe_allow_html=True)
    
    if st.button("Login", key="go_to_login", use_container_width=True):
        st.switch_page("pages/login.py")