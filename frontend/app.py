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

# CSS cho hàng nút cố định chiều rộng và ngang hàng
st.markdown("""
<style>
.action-bar {
    display: flex;
    gap: 14px;
    align-items: center;
    flex-wrap: nowrap;
    margin-top: 8px;
}
.action-bar .stButton > button {
    width: 150px !important;   /* chỉnh chiều rộng ở đây */
    padding: px 4px;
    font-size: 14px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# Thay phần tạo 2 nút (đang dọc) bằng columns để nằm ngang
st.markdown('<div class="right-container"><div class="top-right-actions">', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])
with col_a:
    btn_vao = st.button("Vào lớp", key="vao_lop_btn")
with col_b:
    btn_them = st.button("Thêm lớp học", key="them_lop_btn")

if btn_vao:
    if st.session_state.get("logged_in", False):
        st.switch_page("pages/dashboard.py")
    else:
        st.warning("Bạn cần đăng nhập để vào lớp.")

if btn_them:
    if st.session_state.get("logged_in", False):
        st.switch_page("pages/add_class.py")
    else:
        st.warning("Bạn cần đăng nhập để thêm lớp học.")

st.markdown('</div></div>', unsafe_allow_html=True)