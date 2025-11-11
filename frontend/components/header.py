"""
Header Component
"""
import streamlit as st
from datetime import datetime

def render_header():
    """Render header with date and time"""
    col1, col2 = st.columns([3, 1])
    
    with col2:
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.markdown(f"**{current_date}**")
