import streamlit as st

def render_header(class_name="", full_class_name="", course_code="", class_id=None):
    
    # Tạo một lớp nền background cho header (xử lý bằng CSS)
    st.markdown('<div class="header-background"></div>', unsafe_allow_html=True)

    # Container chứa các ô input
    with st.container():
        # Thêm class để CSS target vào container này đẩy nó lên trên
        st.markdown('<div class="header-input-container">', unsafe_allow_html=True)
        
        # CHIA 3 CỘT ĐỀU NHAU (BỎ 2 CỘT RỖNG 2 BÊN ĐI)
        col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

        with col1:
            st.text_input("Mã lớp", value=class_name, disabled=True, key=f"class_name_{class_id}", placeholder="Lớp")

        with col2:
            st.text_input("Tên môn học", value=full_class_name, disabled=True, key=f"full_class_name_{class_id}", placeholder="Môn học")

        with col3:
            st.text_input("Mã môn", value=course_code, disabled=True, key=f"course_code_{class_id}", placeholder="Mã HP")
            
        st.markdown('</div>', unsafe_allow_html=True)