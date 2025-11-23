import streamlit as st
from pathlib import Path
import sys

# ===== IMPORT SIDEBAR AUTH =====
sys.path.append(str(Path(__file__).parent.parent))
try:
    from components.sidebar_auth import render_auth_sidebar
    from services.api_client import get_all_classes
except ImportError:
    # Mock dữ liệu giống cấu trúc ảnh database bạn gửi
    def render_auth_sidebar(): pass
    def get_all_classes():
        return [
            {"ClassID": 14, "ClassName": "23DHTT01", "FullClassName": "Toán chuyên đề", "CourseCode": "101010101"},
            {"ClassID": 15, "ClassName": "24DHTT03", "FullClassName": "Lập trình", "CourseCode": "10100803"},
            {"ClassID": 16, "ClassName": "25DHTT02", "FullClassName": "Liên Hợp Quốc", "CourseCode": "102"},
            {"ClassID": 17, "ClassName": "24DHDL09", "FullClassName": "Kinh tế vĩ mô", "CourseCode": "109"},
            {"ClassID": 18, "ClassName": "23DHDL02", "FullClassName": "Lập trình Python", "CourseCode": "2102"},
        ]

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Các buổi học", layout="wide", initial_sidebar_state="expanded")

# ===== CSS STYLING =====
st.markdown("""
<style>
    /* 1. Ẩn padding mặc định của Streamlit để giao diện sát lề hơn */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* 2. Style tiêu đề H2 */
    h2 {
        text-align: center;
        color: #0a2540;
        font-weight: 700;
        margin-bottom: 10px;
        margin-top: 0px;
    }

    /* 3. Style ô tìm kiếm (Input) */
    div[data-testid="stTextInput"] > div > div {
        background-color: #f0f2f6;
        border-radius: 10px;
        border: none;
    }

    /* 4. Style Header Bảng */
    .table-header {
        font-size: 16px;
        font-weight: 600;
        color: #666;
        margin-bottom: 10px;
        padding-left: 5px;
    }

    /* 5. STYLE CHO NÚT BẤM DANH SÁCH LỚP (MÀU TRẮNG, CÓ VIỀN) */
    /* Selector này nhắm vào các nút nằm trong cột thứ 2 (cột Tên lớp) */
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button {
        width: 100%;
        background-color: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        text-align: left;
        padding: 10px 15px;
        font-size: 15px;
        transition: all 0.2s;
        min-height: 45px;
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"] button:hover {
        border-color: #0a2540;
        color: #0a2540;
        background-color: #f9f9f9;
    }
    
    /* 6. STYLE ĐẶC BIỆT CHO NÚT BACK (←) */
    /* Selector này nhắm vào nút nằm ở cột đầu tiên (chính là nút Back) */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button {
        background: transparent !important;
        border: none !important;
        font-size: 35px !important;  /* Tăng kích cỡ chữ ở đây */
        font-weight: bold !important;
        color: #0a2540 !important;
        padding: 0px !important;
        line-height: 1 !important;
        min-height: 0px !important;
        margin-top: -5px; /* Đẩy lên một chút cho cân với tiêu đề */
    }
    /* Hiệu ứng khi di chuột vào nút Back */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:hover {
        color: #d9534f !important; /* Đổi màu đỏ khi hover để gây chú ý */
        background: transparent !important;
    }
    
    /* 7. Style ô Mã lớp (CourseCode) - Chỉ hiển thị */
    .class-code-box {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px 15px;
        color: #333;
        font-size: 15px;
        min-height: 45px;
        display: flex;
        align-items: center;
    }

    /* 8. Căn giữa số thứ tự */
    .stt-col {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 45px;
        font-weight: bold;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_auth_sidebar()

# ===== DATA LOGIC =====
classes = get_all_classes() or []

# ===== UI HEADER & BACK BUTTON =====
# Tạo 3 cột: Nút Back | Tiêu đề | Khoảng trống (để cân đối tiêu đề ra giữa)
c_back, c_title, c_void = st.columns([1, 8, 1])
with c_back:
    # Nút quay lại app.py
    if st.button("←", help="Quay lại trang chủ"):
        st.switch_page("app.py")
with c_title:
    st.markdown("<h2>Các buổi học</h2>", unsafe_allow_html=True)


# ===== SEARCH BAR (BÊN TRÁI) =====
# Chia cột để thanh tìm kiếm nằm gọn bên trái (chiếm 30-40% màn hình)
col_search, col_space = st.columns([4, 6]) 
with col_search:
    search_query = st.text_input("Search", placeholder="Tìm kiếm theo tên hoặc mã lớp...", label_visibility="collapsed")

# ===== FILTER LOGIC =====
if search_query:
    search_lower = search_query.lower()
    classes = [
        c for c in classes
        if search_lower in str(c.get("FullClassName", "")).lower() 
        or search_lower in str(c.get("CourseCode", "")).lower()
    ]

st.write("") # Spacer

# ===== TABLE HEADER =====
# Tỷ lệ: STT (0.8) | Tên lớp (4) | Mã lớp (2.5)
c1, c2, c3 = st.columns([0.8, 4, 2.5])

with c1:
    st.markdown('<div class="table-header" style="text-align:center;">STT</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="table-header">Tên lớp</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="table-header">Mã lớp</div>', unsafe_allow_html=True)

# ===== TABLE ROW LOOP =====
for idx, c in enumerate(classes, 1):
    # Lấy dữ liệu theo yêu cầu: FullClassName và CourseCode
    display_name = c.get("FullClassName", "Chưa đặt tên") 
    display_code = c.get("CourseCode", "")
    class_id = c.get("ClassID", idx)
    
    c1, c2, c3 = st.columns([0.8, 4, 2.5])
    
    # Cột 1: STT
    with c1:
        st.markdown(f'<div class="stt-col">{idx}</div>', unsafe_allow_html=True)
        
    # Cột 2: Button (Hiển thị FullClassName)
    with c2:
        if st.button(display_name, key=f"btn_{class_id}", use_container_width=True):
            st.session_state["selected_class_info"] = c
            st.switch_page("pages/class_detail.py")
            
    # Cột 3: Mã lớp (Hiển thị CourseCode)
    with c3:
        st.markdown(f'<div class="class-code-box">{display_code}</div>', unsafe_allow_html=True)
        
    # Spacer row
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)