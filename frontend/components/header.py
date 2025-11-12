# --- File: frontend/components/header.py ---
import streamlit as st
from pathlib import Path


def render_header():
    # ==========================================================
    # 💅 1. Giao diện CSS cho Header
    # ==========================================================
    st.markdown("""
        <style>
          /* Ẩn header và footer mặc định của Streamlit */
          header, footer {visibility: hidden;}

          /* SỬA: Ghi đè padding mặc định của Streamlit */
          div.block-container {
              padding-top: 1rem;     /* Giảm padding trên cùng */
              padding-bottom: 0rem;  /* Giảm padding dưới cùng */
              padding-left: 1.5rem;  /* Tùy chỉnh padding trái */
              padding-right: 1.5rem; /* Tùy chỉnh padding phải */
          }

          /* Container cho toàn bộ Header */
          .main-header-container {
            display: flex;
            align-items: center;
            padding: 10px 0px; /* Bỏ padding trái/phải vì block-container đã xử lý */
            background-color: #f0f2f6; /* Màu nền nhẹ cho Header */
            width: 100%;
          }
          /* Logo và Tên trường */
          .logo-area {
            display: flex;
            align-items: center;
            flex-grow: 1;
            min-width: 250px; 
          }
          .logo-area img {
            height: 40px; /* Điều chỉnh kích thước logo */
          }
          .logo-area .school-name {
            font-size: 10px;
            font-weight: 600;
            margin-left: 5px;
            color: #333;
          }
          /* Các ô input */
          .header-input-container {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-grow: 2; 
          }
          /* ... (phần còn lại của CSS giữ nguyên) ... */
          .header-input-container .stSelectbox,
          .header-input-container .stTextInput {
              min-width: 150px;
              width: 100%;
          }
          .header-input-container .stSelectbox label,
          .header-input-container .stTextInput label {
              font-size: 14px;
              font-weight: 600;
              margin-bottom: 2px;
          }
          .user-icon-placeholder {
            font-size: 28px;
            margin: 0 15px;
            color: #333;
            cursor: pointer;
          }
        </style>
    """, unsafe_allow_html=True)

    # ==========================================================
    # 📝 2. Cấu trúc Header
    # ==========================================================

    # --- SỬA: Thiết lập đường dẫn logo và placeholder ---
    # Đường dẫn này giả định file logo nằm ở: Project/frontend/public/images/logo.png
    # (header.py -> components -> frontend -> public)
    logo_path = Path(__file__).parent.parent / "public" / "images" / "logo.png"
    placeholder_logo = "https://via.placeholder.com/150x40.png?text=Logo+VAA"  # Ảnh thay thế

    # --- SỬA: Lấy dữ liệu động từ st.session_state ---

    # 1. Định nghĩa các options (bạn sẽ thay bằng cách query từ DB)
    lop_options = ["Kỹ thuật HK K45", "K46", "K47", "Quản lý HK K45"]
    mon_options = ["Cơ sở Kỹ thuật", "Thiết bị HK", "Luật HK", "An toàn bay"]

    # 2. Lấy giá trị hiện tại từ session_state (nếu có)
    # Nếu không có, nó sẽ dùng giá trị đầu tiên của list làm mặc định
    selected_lop = st.session_state.get("selected_lop", lop_options[0])
    selected_mon = st.session_state.get("selected_mon", mon_options[0])
    selected_ma_mon = st.session_state.get("selected_ma_mon", "")  # Mã môn học

    # 3. Tìm index của giá trị đã chọn (cần cho st.selectbox)
    try:
        lop_index = lop_options.index(selected_lop)
    except ValueError:
        lop_index = 0  # Nếu không tìm thấy, dùng index 0
    try:
        mon_index = mon_options.index(selected_mon)
    except ValueError:
        mon_index = 0

    # 4. Hàm callback để cập nhật lại session_state khi người dùng đổi lựa chọn
    def update_header_selection():
        st.session_state.selected_lop = st.session_state.header_lop
        st.session_state.selected_mon = st.session_state.header_mon
        st.session_state.selected_ma_mon = st.session_state.header_ma_mon

    # --- Bắt đầu vẽ giao diện ---
    with st.container():
        st.markdown("<div class='main-header-container'>", unsafe_allow_html=True)

        # 1. Khu vực Logo và Tên trường
        col_logo, col_inputs, col_user = st.columns([1, 3, 0.2], gap="small")

        with col_logo:
            st.markdown("<div class='logo-area'>", unsafe_allow_html=True)
            if logo_path.exists():
                st.image(str(logo_path), use_column_width=False)
            else:
                # SỬA: Hiển thị ảnh placeholder thay vì st.warning
                st.image(placeholder_logo, use_column_width=False)
            st.markdown("<div class='school-name'>VIETNAM AVIATION ACADEMY</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. Khu vực các ô input (đã được liên kết với session_state)
        with col_inputs:
            col_lop, col_mon, col_ma = st.columns(3)

            with col_lop:
                st.selectbox(
                    "Lớp:",
                    lop_options,
                    index=lop_index,
                    key="header_lop",
                    on_change=update_header_selection
                )

            with col_mon:
                st.selectbox(
                    "Môn:",
                    mon_options,
                    index=mon_index,
                    key="header_mon",
                    on_change=update_header_selection
                )

            with col_ma:
                st.text_input(
                    "Mã môn học:",
                    value=selected_ma_mon,
                    key="header_ma_mon",
                    on_change=update_header_selection,
                    placeholder="Nhập mã môn học"
                )

        # 3. Biểu tượng người dùng
        with col_user:
            st.markdown("<div class='user-icon-placeholder'>👤</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Giữ lại đường kẻ ngang
    st.markdown("<hr style='margin: 0; border: none; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- Hết file component ---