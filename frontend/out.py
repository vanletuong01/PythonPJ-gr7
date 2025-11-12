import streamlit as st
from components.sidebar import render_auth_sidebar
from utils.api_client import get_teacher_classes
from utils.auth_manager import init_auth_state, check_auth, clear_auth_state
import base64
from pathlib import Path

# Cấu hình trang
st.set_page_config(
    page_title="Học Viện Hàng Không Việt Nam",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Khởi tạo auth state
init_auth_state()

# Kiểm tra authentication khi load trang
check_auth()

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
    st.warning(f"Background image not found at: {bg_image_path}")
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


if not st.session_state.logged_in:
    st.markdown('''
        <div class="right-container">
            <div class="top-right-actions">
                <button class="action-btn">Vào lớp</button>
                <button class="action-btn">Thêm lớp học</button>
            </div>
        </div>
    ''', unsafe_allow_html=True)

else:
    st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #667eea;">Chào mừng, {st.session_state.teacher['name']}!</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Lấy danh sách lớp
    try:
        classes_data = get_teacher_classes(st.session_state.teacher['id'])
        classes = classes_data.get('classes', [])
        
        if classes:
            st.success(f"Bạn đang phụ trách {len(classes)} lớp học")
            
            # Hiển thị danh sách lớp
            st.markdown("###Lớp học của tôi")
            
            cols = st.columns(3)
            for idx, cls in enumerate(classes):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                            <div style="background: white; padding: 20px; border-radius: 10px; 
                                        box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
                                <h3 style="color: #667eea; margin-bottom: 10px;">{cls['ClassName']}</h3>
                                <p><strong>Học kỳ:</strong> {cls['Semester']}</p>
                                <p><strong>Sỉ số:</strong> {cls['Quantity']} sinh viên</p>
                                <p><strong>Ca học:</strong> {cls.get('ShiftName', 'N/A')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Vào lớp {cls['ClassName']}", key=f"enter_{idx}"):
                            st.session_state.selected_class = cls
                            st.success(f"Đã chọn lớp {cls['ClassName']}")
                            st.info("Sử dụng menu bên trái để điểm danh hoặc xem báo cáo")
        else:
            st.warning("Bạn chưa được phân công lớp nào. Vui lòng liên hệ quản lý.")
            
    except Exception as e:
        st.error(f"Lỗi tải danh sách lớp: {e}")
        st.info("Vui lòng kiểm tra backend đã chạy chưa")
    
    st.markdown("---")
    st.markdown("### Hướng dẫn")
