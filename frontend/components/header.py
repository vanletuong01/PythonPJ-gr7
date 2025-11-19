import streamlit as st
from pathlib import Path

def render_header(class_name="", full_class_name="", course_code="", class_id=None):
    header_container = st.container()
    key_prefix = f"{class_id}_" if class_id else ""
    with header_container:
        col1, col2, col3, col4, col5 = st.columns([2.5, 1.7, 1.7, 1.7, 2])

        # Cột 1: Title (bỏ logo)
        with col1:
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
                key=f"{key_prefix}filter_class",
                label_visibility="collapsed"
            )

        # Cột 3: Filter Môn
        with col3:
            filter_mon = st.text_input(
                "Môn", 
                value=full_class_name,
                placeholder="Môn:", 
                key=f"{key_prefix}filter_subject",
                label_visibility="collapsed"
            )

        # Cột 4: Filter Mã môn học
        with col4:
            filter_ma_mon = st.text_input(
                "Mã môn học", 
                value=str(course_code) if course_code else "",
                placeholder="Mã môn học:", 
                key=f"{key_prefix}filter_code",
                label_visibility="collapsed"
            )

        # Cột 5: Spacer (bỏ user icon)
        with col5:
            st.write("")

    return filter_lop, filter_mon, filter_ma_mon
