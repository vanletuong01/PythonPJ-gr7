"""
Auth Manager - Quản lý authentication state và token
"""
import streamlit as st
from utils.api_client import verify_token
import json


def save_auth_state(token, teacher):
    """Lưu authentication state vào session và localStorage"""
    st.session_state.logged_in = True
    st.session_state.token = token
    st.session_state.teacher = teacher
    
    # Lưu vào localStorage qua JavaScript
    auth_data = {
        "token": token,
        "teacher": teacher
    }
    
    st.markdown(f"""
        <script>
            localStorage.setItem('auth_data', '{json.dumps(auth_data)}');
        </script>
    """, unsafe_allow_html=True)


def clear_auth_state():
    """Xóa authentication state"""
    st.session_state.logged_in = False
    st.session_state.token = None
    st.session_state.teacher = None
    st.session_state.selected_class = None
    
    # Xóa localStorage
    st.markdown("""
        <script>
            localStorage.removeItem('auth_data');
        </script>
    """, unsafe_allow_html=True)


def check_auth():
    """Kiểm tra authentication state khi load app"""
    # Nếu đã có session state, kiểm tra token có còn valid không
    if st.session_state.get('logged_in') and st.session_state.get('token'):
        token = st.session_state.token
        result = verify_token(token)
        
        if result.get('success'):
            # Token còn hợp lệ, cập nhật thông tin teacher
            st.session_state.teacher = result['teacher']
            return True
        else:
            # Token hết hạn, clear state
            clear_auth_state()
            return False
    
    return False


def init_auth_state():
    """Khởi tạo authentication state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'teacher' not in st.session_state:
        st.session_state.teacher = None
    if 'selected_class' not in st.session_state:
        st.session_state.selected_class = None
