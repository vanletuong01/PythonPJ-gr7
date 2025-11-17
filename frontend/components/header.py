import streamlit as st
from pathlib import Path

def render_header():
    """
    Header cố định ở top với:
    - Logo to + Title
    - 3 filters
    - User icon
    """
    
    # CSS cho header
    st.markdown("""
    <style>
    .header-vaa {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        padding: 18px 28px;
        border-radius: 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        flex-wrap: wrap;
        gap: 14px;
    }
    
    .logo-vaa {
        display: flex;
        align-items: center;
        gap: 12px;
        color: white;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.5px;
    }
    
    .logo-vaa img {
        width: 100px;
        height: 100px;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
    }
    
    .filter-row-header {
        display: flex;
        gap: 10px;
        flex: 1;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .filter-input-header {
        padding: 8px 14px;
        border: none;
        border-radius: 10px;
        font-size: 14px;
        width: 160px;
        outline: none;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    

    
    @media (max-width: 768px) {
        .header-vaa {
            flex-direction: column;
        }
        .filter-row-header {
            width: 100%;
        }
        .filter-input-header {
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render header
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    logo_html = f'<img src="data:image/png;base64,..." alt="logo"/>' if not logo_path.exists() else f'<svg viewBox="0 0 60 60" width="50" height="50"><polygon points="10,50 30,10 50,50" fill="#1e40af"/><path d="M25,25 L35,25 L30,35 Z" fill="#3b82f6"/></svg>'
    
    st.markdown(f"""
    <div class="header-vaa">
        <div class="logo-vaa">
            {logo_html}
            <span>VIETNAM AVIATION ACADEMY</span>
        </div>
        <div class="filter-row-header">
            <input type="text" placeholder="Lớp:" class="filter-input-header" id="class-filter"/>
            <input type="text" placeholder="Môn:" class="filter-input-header" id="subject-filter"/>
            <input type="text" placeholder="Mã môn học:" class="filter-input-header" id="code-filter"/>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Return filters (nếu cần xử lý Streamlit widget)
    return None, None, None
def render_header(class_name="", full_class_name="", course_code=""):
    header_container = st.container()
    
    with header_container:
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
                value=class_name,
                placeholder="Lớp:", 
                key="filter_class",
                label_visibility="collapsed"
            )
        
        # Cột 3: Filter Môn
        with col3:
            filter_mon = st.text_input(
                "Môn", 
                value=full_class_name,
                placeholder="Môn:", 
                key="filter_subject",
                label_visibility="collapsed"
            )
        
        # Cột 4: Filter Mã môn học
        with col4:
            filter_ma_mon = st.text_input(
                "Mã môn học", 
                value=str(course_code) if course_code else "",
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
