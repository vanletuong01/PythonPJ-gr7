import streamlit as st
from pathlib import Path

def render_dashboard_sidebar():
    """Sidebar cho dashboard sau khi login"""
    
    # --- CSS TÙY CHỈNH GIAO DIỆN ---
    st.markdown("""
        <style>
        /* 1. XÓA KHOẢNG TRẮNG TRÊN LOGO */
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* 2. CĂN GIỮA LOGO & TEXT */
        [data-testid="stSidebar"] img {
            display: block;
            margin: 0 auto;
        }
        .sidebar-text {
            text-align: center;
            color: #333;
        }
        .teacher-box {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }

        /* 3. STYLE NÚT BẤM (MÀU NHẠT, TINH TẾ) */
        div.stButton > button {
            width: 100%;
            background-color: #ffffff !important;
            color: #444 !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            transition: all 0.3s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }

        div.stButton > button:hover {
            background-color: #f0f7ff !important;
            border-color: #0a2540 !important;
            color: #0a2540 !important;
            transform: translateY(-1px);
        }

        /* 4. NÚT ĐĂNG XUẤT (MÀU ĐỎ NHẠT) */
        [data-testid="stSidebar"] div.stButton:last-of-type > button {
            background-color: #fff5f5 !important;
            color: #c0392b !important;
            border: 1px solid #fadbd8 !important;
            margin-top: 20px !important;
        }
        
        [data-testid="stSidebar"] div.stButton:last-of-type > button:hover {
            background-color: #fee2e2 !important;
            border-color: #e74c3c !important;
            font-weight: 700 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # --- LOGO ---
        logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=400)
        
        st.markdown("""
            <div class="sidebar-text">
                <h3 style="margin: 10px 0 5px 0; font-size: 20px; font-weight: 700; color: #0a2540;">VIETNAM AVIATION ACADEMY</h3>
                <p style="font-size: 16px; color: #666; margin-bottom: 15px;">Hệ thống điểm danh sinh viên</p>
            </div>
        """, unsafe_allow_html=True)
        
        # --- THÔNG TIN GIÁO VIÊN ---
        teacher = st.session_state.get("teacher", {})
        name = teacher.get("name", "Giáo viên")
        email = teacher.get("email", "")
        
        st.markdown(f"""
            <div class="teacher-box">
                <div style="font-weight: 1000; font-size: 20px; color: #111;">👤 {name}</div>
                <div style="font-size: 20px; color: #777; margin-top: 4px;">{email}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- MENU NAVIGATION ---
        st.markdown("<p style='font-size: 12px; color: #999; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;'>Menu Quản lý</p>", unsafe_allow_html=True)
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")
        
        if st.button("➕ Thêm lớp học", use_container_width=True):
            st.switch_page("pages/add_class.py")
        
        if st.button("👨‍🎓 Thêm sinh viên", use_container_width=True):
            st.switch_page("pages/add_student.py")
        
        if st.button("✅ Điểm danh", use_container_width=True):
            st.switch_page("pages/select_session.py")
        
        if st.button("❌ Thoát lớp ", use_container_width=True):
            st.switch_page("pages/join_class.py")
       


        # --- LOGOUT ---
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.switch_page("pages/login.py")