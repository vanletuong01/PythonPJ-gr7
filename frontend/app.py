import streamlit as st
from components.sidebar_auth import render_auth_sidebar
import base64
from pathlib import Path

# Cấu hình trang
st.set_page_config(
    page_title="Học Viện Hàng Không Việt Nam",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Khởi tạo session state mặc định
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher" not in st.session_state:
    st.session_state.teacher = {}

# Load và encode background image
def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def load_css(file_path):
    """Load CSS from external file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

# Load CSS từ file
css_path = Path(__file__).parent / "public" / "css" / "out.css"
css_content = load_css(str(css_path))
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# Load background image
bg_image_path = Path(__file__).parent / "public" / "images" / "background.png"
if not bg_image_path.exists():
    st.warning(f"Background không được tìm thấy tại: {bg_image_path}")
bg_base64 = get_base64_image(str(bg_image_path)) if bg_image_path.exists() else None

if bg_base64:
    st.markdown(f"""
        <style>
        .right-container {{
            background-image: url('data:image/png;base64,{bg_base64}');
        }}
        </style>
    """, unsafe_allow_html=True)

render_auth_sidebar()

st.markdown('<div class="right-container"><div class="top-right-actions">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    st.button("Vào lớp", key="vao_lop_btn")
with col2:
    if st.button("Thêm lớp học", key="them_lop_btn"):
        if st.session_state.get("logged_in", False):
            st.switch_page("pages/add_class.py")
        else:
            st.warning("Bạn cần đăng nhập để thêm lớp học.")
st.markdown('</div></div>', unsafe_allow_html=True)