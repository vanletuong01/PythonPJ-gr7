"""
Header Component - Fixed gradient bar with filters
"""
import streamlit as st
from pathlib import Path

def render_header():
    """
    Header cố định ở top với:
    - Logo to + Title
    - 3 filters
    - User icon
    """
    
    header_container = st.container()
    
    with header_container:
        # Layout: Logo+Title(25%) | Filter1(17%) | Filter2(17%) | Filter3(17%) | Spacer(20%) | Icon(4%)
        col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1.7, 1.7, 1.7, 2, 0.4])
        
        # Cột 1: Logo + Title
        with col1:
            subcol_logo, subcol_title = st.columns([0.5, 2])
            with subcol_logo:
                logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
                if logo_path.exists():
                    st.image(str(logo_path), width=70)
            with subcol_title:
                st.markdown("""
                <div style='color:white;margin-top:14px'>
                    <h3 style='margin:0;font-size:20px;font-weight:700;line-height:1.2'>
                        VIETNAM AVIATION ACADEMY
                    </h3>
                </div>
                """, unsafe_allow_html=True)
        
        # Cột 2: Filter Lớp
        with col2:
            filter_lop = st.text_input(
                "Lớp", 
                placeholder="Lớp:", 
                key="filter_class",
                label_visibility="collapsed"
            )
        
        # Cột 3: Filter Môn
        with col3:
            filter_mon = st.text_input(
                "Môn", 
                placeholder="Môn:", 
                key="filter_subject",
                label_visibility="collapsed"
            )
        
        # Cột 4: Filter Mã môn học
        with col4:
            filter_ma_mon = st.text_input(
                "Mã môn học", 
                placeholder="Mã môn học:", 
                key="filter_code",
                label_visibility="collapsed"
            )
        
        # Cột 5: Spacer (để đẩy icon sang phải)
        with col5:
            st.write("")
        
        # Cột 6: User Icon
        with col6:
            st.markdown("""
            <div style='text-align:center;margin-top:10px;font-size:32px;color:white;cursor:pointer'>
                👤
            </div>
            """, unsafe_allow_html=True)
    
    return filter_lop, filter_mon, filter_ma_mon
