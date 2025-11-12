import streamlit as st
from pathlib import Path

st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                background-color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)

def render_auth_sidebar():
    with st.sidebar:
        if st.session_state.get('logged_in', False):
            # Hiện tên giáo viên
            st.markdown(f"""
                <div class="user-info">
                    <div class="user-details">
                        <div class="user-name">{st.session_state.teacher['name']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="sidebar-auth-links">
                    <a href="/login" target="_self">Đăng nhập</a>
                    <span>/</span>
                    <a href="/register" target="_self">Đăng ký</a>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
    
        # Logo
        logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=180)
        # Tên trường
        st.markdown("""
            <div class="sidebar-school-title">
                <p>VIETNAM AVIATION ACADEMY</p>
                <p>Học Viện Hàng Không<br>Việt Nam</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 15px 0;'><hr style='margin: 0; border: none; border-top: 1px solid #000000;'></div>", unsafe_allow_html=True)
    
        # Logged in state - show logout button
        if st.session_state.get('logged_in', False):
            # Dòng chào mừng
            st.markdown("""
                <p style="text-align: center; font-size: 11px; color: #888; line-height: 1.4;">
                    Chào mừng tới trang<br>điểm danh sinh viên
                </p>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
            
            if st.button("Đăng xuất"):
                st.session_state.logged_in = False
                st.session_state.teacher = {}
                st.rerun()
        else:
            # Dòng chào mừng khi chưa đăng nhập
            st.markdown("""
                <p style="text-align: center; font-size: 11px; color: #888; line-height: 1.4;">
                    Chào mừng tới trang<br>điểm danh sinh viên
                </p>
            """, unsafe_allow_html=True)
