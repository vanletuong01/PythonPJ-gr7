import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta

# ===== IMPORT COMPONENTS =====
sys.path.append(str(Path(__file__).parent.parent))
try:
    from components.sidebar_auth import render_auth_sidebar
    # Import các hàm cần thiết
    from services.api_client import get_attendance_session_detail, get_students_in_class
except ImportError:
    # Mock data phòng hờ
    def render_auth_sidebar(): pass
    def get_students_in_class(class_id): return []
    def get_attendance_session_detail(class_id, date): return []

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Chi tiết lớp học", layout="wide", initial_sidebar_state="expanded")

# ===== CSS STYLING (GIỮ NGUYÊN DESIGN ĐẸP CỦA BẠN) =====
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    .class-info-header { display: flex; gap: 30px; margin-bottom: 20px; font-size: 16px; color: #333; }
    
    /* Style Input và Selectbox */
    div[data-testid="stTextInput"] > div > div, div[data-testid="stSelectbox"] > div > div {
        background-color: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
    }
    
    /* Header List */
    .list-header { display: flex; padding: 10px 20px; font-weight: 600; color: #555; margin-top: 20px; }
    
    /* Student Card */
    .student-card {
        background-color: white; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 15px 20px; margin-bottom: 10px; display: flex; align-items: center;
        transition: box-shadow 0.2s;
    }
    .student-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-color: #ccc; }
    
    /* Nút Back to đẹp */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button {
        background: transparent !important; border: none !important; font-size: 30px !important;
        font-weight: bold !important; color: #0a2540 !important; padding: 0px !important;
        line-height: 1 !important; margin-top: -5px;
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:hover { color: #d9534f !important; }
    
    /* Status Colors */
    .status-ok { color: #28a745; font-weight: 500; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
    .status-miss { color: #333; font-weight: 500; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
    .status-absent { color: #dc3545; font-weight: 500; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
</style>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
render_auth_sidebar()

# ===== HEADER & BACK BUTTON =====
col_back, col_title = st.columns([0.5, 9.5])
with col_back:
    if st.button("←", help="Quay lại"):
        st.switch_page("pages/all_class.py")
with col_title:
    st.markdown("<h2 style='margin:0; color:#0a2540;'>Chi tiết lớp học</h2>", unsafe_allow_html=True)

# ===== LẤY THÔNG TIN LỚP =====
class_info = st.session_state.get("selected_class_info", {})
class_id = class_info.get("ClassID")

# Hiển thị thông tin chung
st.markdown(
    f"""
    <div class="class-info-header" style="justify-content: center; margin-top: 10px;">
        <div><b>Lớp:</b> {class_info.get('ClassName', 'N/A')}</div>
        <div><b>Môn:</b> {class_info.get('FullClassName', class_info.get('SubjectName', 'N/A'))}</div>
        <div><b>Mã môn học:</b> {class_info.get('CourseCode', class_info.get('ClassCode', 'N/A'))}</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# ===== [LOGIC MỚI] TẠO DANH SÁCH BUỔI HỌC (BUỔI 1 - NGÀY ...) =====
session_options = [] # List chứa dict: {'label': 'Buổi 1 - ...', 'value': '2025-11-20'}

try:
    # Lấy ngày bắt đầu và kết thúc từ API (hoặc default nếu thiếu)
    date_start_str = str(class_info.get("DateStart", "2025-09-08")) # Giá trị mặc định để test
    date_end_str = str(class_info.get("DateEnd", "2026-01-15"))    # Giá trị mặc định để test
    
    start_date = datetime.strptime(date_start_str, "%Y-%m-%d")
    end_date = datetime.strptime(date_end_str, "%Y-%m-%d")
    
    current_date = start_date
    idx = 1
    
    # Vòng lặp tạo từng buổi (mỗi tuần 1 buổi)
    while current_date <= end_date:
        d_str = current_date.strftime("%d/%m/%Y")      # Format hiển thị (20/11/2025)
        v_str = current_date.strftime("%Y-%m-%d")      # Format gửi API (2025-11-20)
        
        session_options.append({
            "label": f"Buổi {idx} - {d_str}",
            "value": v_str
        })
        
        current_date += timedelta(weeks=1) # Cộng thêm 1 tuần
        idx += 1
        
        if idx > 50: break # Safety break
        
except Exception as e:
    st.error(f"Lỗi tính toán lịch học: {e}")

# ===== THANH ĐIỀU KHIỂN (TÌM KIẾM & CHỌN BUỔI) =====
col_search, col_space, col_filter = st.columns([4, 2, 3])

with col_search:
    search_text = st.text_input("Tìm kiếm", placeholder="Tìm kiếm sinh viên...", label_visibility="collapsed")

selected_date_api = None

with col_filter:
    if session_options:
        # Dropdown hiển thị "Buổi X - Ngày Y"
        selected_idx = st.selectbox(
            "Chọn buổi", 
            range(len(session_options)), 
            format_func=lambda i: session_options[i]["label"], # Hiển thị Label
            label_visibility="collapsed"
        )
        # Lấy giá trị ngày thực tế để gọi API (YYYY-MM-DD)
        selected_date_api = session_options[selected_idx]["value"]
    else:
        st.selectbox("Chọn buổi", ["Chưa có lịch học"], disabled=True, label_visibility="collapsed")


# ===== XỬ LÝ DỮ LIỆU SINH VIÊN & ĐIỂM DANH =====

# 1. Lấy toàn bộ sinh viên trong lớp
all_students = get_students_in_class(class_id) or []

# 2. Lấy trạng thái điểm danh của ngày được chọn
attendance_map = {}
if selected_date_api:
    attendance_records = get_attendance_session_detail(class_id, selected_date_api) or []
    for rec in attendance_records:
        mssv = str(rec.get("StudentCode", "")).strip()
        attendance_map[mssv] = rec.get("Status", "")

# 3. Ghép danh sách (Merge)
final_list = []
for sv in all_students:
    sv_name = sv.get("StudentName") or sv.get("FullName") or "Unknown"
    sv_code = str(sv.get("StudentCode", "")).strip()
    
    # Tra cứu trạng thái
    status = attendance_map.get(sv_code, "Chưa điểm danh")
    
    final_list.append({
        "FullName": sv_name,
        "StudentCode": sv_code,
        "Status": status
    })

# 4. Lọc tìm kiếm
if search_text:
    s_lower = search_text.lower()
    final_list = [s for s in final_list if s_lower in str(s["FullName"]).lower() or s_lower in str(s["StudentCode"]).lower()]

# ===== HIỂN THỊ DANH SÁCH =====
st.markdown("""
    <div class="list-header">
        <div style="flex: 0.5; text-align: center;">STT</div>
        <div style="flex: 3;">Họ và Tên</div>
        <div style="flex: 2;">Mssv</div>
        <div style="flex: 2; text-align: right;">Tình trạng</div>
    </div>
""", unsafe_allow_html=True)

if not final_list:
    st.info("Không tìm thấy sinh viên nào.")
else:
    for idx, sv in enumerate(final_list, 1):
        name = sv["FullName"]
        mssv = sv["StudentCode"]
        raw_status = sv["Status"]
        
        status_str = str(raw_status).lower()
        if "đã" in status_str or "present" in status_str or raw_status is True:
            status_html = f'<div class="status-ok">Đã điểm danh <span style="font-size:18px;">✔️</span></div>'
        elif "vắng" in status_str or "absent" in status_str:
             status_html = f'<div class="status-absent">Vắng <span style="font-size:18px;">❌</span></div>'
        else:
            status_html = f'<div class="status-miss">Chưa điểm danh <span style="font-size:18px; font-weight:bold; color:black;">✕</span></div>'

        st.markdown(
            f"""
            <div class="student-card">
                <div style="flex: 0.5; text-align: center; color: #888; font-weight: bold;">{idx}</div>
                <div style="flex: 3; font-weight: 500; color: #333;">{name}</div>
                <div style="flex: 2; color: #666;">{mssv}</div>
                <div style="flex: 2;">{status_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )