"""
Register Page
"""
import streamlit as st
from pathlib import Path
from utils.api_client import register_teacher
from utils.auth_manager import init_auth_state

# Khởi tạo auth state
init_auth_state()

# Cấu hình trang
st.set_page_config(
    page_title="Đăng ký - VAA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS cho trang register
st.markdown("""
    <style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hide sidebar completely with all navigation */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    nav {
        display: none !important;
    }
    
    .css-1d391kg {
        display: none !important;
    }
    
    .main {
        padding: 0 !important;
        background: white;
    }
    
    .block-container {
        padding: 2rem 1rem !important;
        max-width: 100% !important;
    }
    
    /* Register container */
    .register-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        gap: 50px;
    }
    
    .register-left {
        flex: 1;
        text-align: center;
    }
    
    .register-right {
        flex: 1;
        max-width: 400px;
    }
    
    .register-illustration {
        max-width: 100%;
        height: auto;
    }
    
    .logo-register {
        width: 120px;
        margin-bottom: 20px;
    }
    
    .register-title {
        font-size: 28px;
        font-weight: 700;
        color: #333;
        margin-bottom: 10px;
    }
    
    .register-subtitle {
        font-size: 14px;
        color: #888;
        margin-bottom: 30px;
    }
    
    /* Form styling */
    .stTextInput > label {
        font-size: 14px;
        color: #333;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 12px;
        font-size: 14px;
    }
    
    .stButton > button {
        width: 100%;
        background: #000;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 14px;
        font-weight: 600;
        font-size: 15px;
        margin-top: 10px;
    }
    
    .stButton > button:hover {
        background: #333;
    }
    
    .login-link {
        text-align: center;
        margin-top: 20px;
        font-size: 13px;
        color: #666;
    }
    
    .login-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

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
                <h1 style="color: #667eea; font-size: 48px;">🔐</h1>
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
        email = st.text_input("Email", placeholder="Enter your email", label_visibility="visible")
        password = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="visible")
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                try:
                    st.info(f"Đang đăng ký với email: {email}")
                    result = register_teacher(
                        name=email.split('@')[0],  # Tạm dùng email prefix làm name
                        email=email,
                        password=password,
                        phone=""  # Có thể thêm field phone nếu cần
                    )
                    
                    st.info(f"Response từ API: {result}")  # Debug log
                    
                    if result and result.get('success'):
                        st.success("Registration successful! Redirecting to login...")
                        st.balloons()
                        # Redirect to login page
                        import time
                        time.sleep(2)
                        st.switch_page("pages/login.py")
                    else:
                        st.error(f"Lỗi: {result.get('message', 'Registration failed')}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Login link - button instead of HTML link
    col_link1, col_link2, col_link3 = st.columns([1, 2, 1])
    with col_link2:
        st.markdown('<div style="text-align: center; margin-top: 20px; font-size: 13px; color: #666;">Have an account?</div>', unsafe_allow_html=True)
        if st.button("Login", key="go_to_login", use_container_width=True):
            st.switch_page("pages/login.py")
