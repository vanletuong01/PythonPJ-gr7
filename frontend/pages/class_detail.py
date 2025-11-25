import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta

# ===== IMPORT COMPONENTS =====
sys.path.append(str(Path(__file__).parent.parent))
try:
    from components.sidebar_auth import render_auth_sidebar
    # Import các hàm cần thiết
    from services.api_client import get_session_detail, get_students_in_class
except ImportError:
    def render_auth_sidebar(): pass
    def get_students_in_class(class_id): return []
    def get_session_detail(class_id, date): return {}

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Chi tiết lớp học", layout="wide", initial_sidebar_state="expanded")

# ===== CSS STYLING =====
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    .class-info-header { display: flex; gap: 30px; margin-bottom: 20px; font-size: 16px; color: #333; }
    div[data-testid="stTextInput"] > div > div, div[data-testid="stSelectbox"] > div > div {
        background-color: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
    }
    .list-header { display: flex; padding: 10px 20px; font-weight: 600; color: #555; margin-top: 20px; }
    .student-card {
        background-color: white; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 15px 20px; margin-bottom: 10px; display: flex; align-items: center;
        transition: box-shadow 0.2s;
    }
    .student-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-color: #ccc; }
    
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button {
        background: transparent !important; border: none !important; font-size: 30px !important;
        font-weight: bold !important; color: #0a2540 !important; padding: 0px !important;
        line-height: 1 !important; margin-top: -5px;
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"] button:hover { color: #d9534f !important; }
    
    .status-ok { color: #28a745; font-weight: 700; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
    .status-miss { color: #333; font-weight: 500; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
    .status-absent { color: #dc3545; font-weight: 600; display: flex; align-items: center; justify-content: flex-end; gap: 5px;}
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

if not class_id:
    st.warning("Vui lòng chọn lớp học trước!")
    st.stop()

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

# ===== TẠO LIST BUỔI HỌC =====
session_options = [] 
try:
    date_start_str = str(class_info.get("DateStart", "2025-01-01")) 
    date_end_str = str(class_info.get("DateEnd", "2026-01-01"))    
    
    start_date = datetime.strptime(date_start_str, "%Y-%m-%d")
    end_date = datetime.strptime(date_end_str, "%Y-%m-%d")
    
    current_date = start_date
    idx = 1
    while idx <= 15 and current_date <= end_date:
        d_str = current_date.strftime("%d/%m/%Y")
        v_str = current_date.strftime("%Y-%m-%d")
        session_options.append({"label": f"Buổi {idx} - {d_str}", "value": v_str})
        current_date += timedelta(weeks=1)
        idx += 1
except Exception as e:
    st.error(f"Lỗi lịch học: {e}")

# ===== SEARCH & FILTER =====
col_search, col_space, col_filter = st.columns([4, 2, 3])

with col_search:
    search_text = st.text_input("Tìm kiếm", placeholder="Tìm kiếm sinh viên...", label_visibility="collapsed")

selected_date_api = None
with col_filter:
    if session_options:
        selected_idx = st.selectbox("Chọn buổi", range(len(session_options)), format_func=lambda i: session_options[i]["label"], label_visibility="collapsed")
        selected_date_api = session_options[selected_idx]["value"]
    else:
        st.selectbox("Chọn buổi", ["Chưa có lịch"], disabled=True)

# =========================================================
# 3. XỬ LÝ DỮ LIỆU (QUAN TRỌNG: ĐÃ SỬA LOGIC)
# =========================================================

# B1: Lấy danh sách tất cả sinh viên trong lớp
all_students = get_students_in_class(class_id) or []

# B2: Lấy dữ liệu điểm danh (API trả về Dict: {success, attended_list, absent_list})
attendance_map = {} # Map lưu trạng thái: { MSSV : "Đã điểm danh" }

if selected_date_api:
    # Gọi API get_session_detail (chứ không phải get_attendance_session_detail cũ)
    resp = get_session_detail(class_id, selected_date_api)
    
    if isinstance(resp, dict) and resp.get("success"):
        # Lấy danh sách ĐÃ ĐIỂM DANH từ API response
        attended_list = resp.get("attended_list", [])
        
        # Duyệt qua danh sách đã điểm danh để đánh dấu vào Map
        for s in attended_list:
            mssv = str(s.get("StudentCode", "")).strip()
            attendance_map[mssv] = "Đã điểm danh"

# B3: Ghép dữ liệu (Merge)
final_list = []
for sv in all_students:
    # Lấy tên và MSSV từ danh sách gốc
    sv_name = sv.get("StudentName") or sv.get("FullName") or "Unknown"
    sv_code = str(sv.get("StudentCode", "")).strip()
    
    # Kiểm tra trong Map điểm danh
    if sv_code in attendance_map:
        status = "Đã điểm danh"
    else:
        status = "Chưa điểm danh"
    
    final_list.append({
        "FullName": sv_name,
        "StudentCode": sv_code,
        "Status": status
    })

# B4: Lọc theo ô tìm kiếm
if search_text:
    s_lower = search_text.lower()
    final_list = [s for s in final_list if s_lower in str(s["FullName"]).lower() or s_lower in str(s["StudentCode"]).lower()]

# ===== HIỂN THỊ UI =====
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
        status = sv["Status"]
        
        # Logic hiển thị HTML status
        if status == "Đã điểm danh":
            status_html = f'<div class="status-ok">Đã điểm danh <span style="font-size:18px;">✔️</span></div>'
        else:
            status_html = f'<div class="status-miss">Chưa điểm danh <span style="font-size:18px; font-weight:bold; color:#ccc;">✕</span></div>'

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