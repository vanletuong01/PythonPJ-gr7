import streamlit as st
from pathlib import Path
import datetime
from components.sidebar_auth import render_auth_sidebar
from services.api_client import get_majors, get_types, get_classes_by_teacher, get_shifts

# ==== PAGE CONFIG ====
st.set_page_config(page_title="Vào lớp", layout="wide", initial_sidebar_state="collapsed")

# ==== LOAD CSS ====
css_path = Path(__file__).parent.parent / "public" / "css" / "join_class.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ==== CHECK LOGIN ====
if not st.session_state.get("logged_in", False) or not st.session_state.get("teacher", {}).get("id_login"):
    st.warning("Bạn cần đăng nhập để vào lớp.")
    st.switch_page("app.py")
    st.stop()

# ==== LAYOUT ====
render_auth_sidebar()

# --- TIÊU ĐỀ ---
col_back, col_title = st.columns([0.15, 6])
with col_back:
    if st.button("←", key="back_add_class", help="Quay về trang thêm lớp"):
        st.switch_page("app.py")
with col_title:
    st.markdown("""
        <div class="page-header">
            <h1 class="page-title">VÀO LỚP HỌC</h1>
            <p class="page-subtitle">Tìm kiếm lớp học hoặc lọc theo chuyên ngành</p>
        </div>
    """, unsafe_allow_html=True)

teacher = st.session_state.get("teacher")
id_login = teacher.get("id_login")

# --- DATA LOADING ---
majors = get_majors() or []
types = get_types() or []
shifts = get_shifts() or []
class_list = get_classes_by_teacher(id_login) or []
    
major_dict = {m['MajorID']: m['MajorName'] for m in majors}
type_dict = {t['TypeID']: t['TypeName'] for t in types}
shift_dict = {s['ShiftID']: s['ShiftName'] for s in shifts}
class_options = {c["ClassID"]: c for c in class_list}

# Khởi tạo state cho bộ lọc
if "filter_major" not in st.session_state: st.session_state.filter_major = None
if "filter_type" not in st.session_state: st.session_state.filter_type = None
if "selected_class_id" not in st.session_state: st.session_state.selected_class_id = None

# ==========================================
# 1. PHẦN TÌM KIẾM
# ==========================================
s_col1, s_col2 = st.columns([4, 1])
with s_col1:
    search_text = st.text_input("Tìm kiếm nhanh", placeholder="Nhập tên lớp, mã môn học...", label_visibility="collapsed")
with s_col2:
    if st.button("🔍 Tìm kiếm", use_container_width=True):
        found = None
        q = (search_text or "").strip().lower()
        if q:
            for c in class_list:
                c_str = str(c).lower()
                if q in c_str:
                    found = c
                    break
        if found:
            st.session_state.filter_major = None
            st.session_state.filter_type = None
            st.session_state.selected_class_id = found["ClassID"]
            st.toast(f"Đã tìm thấy: {found.get('ClassName')}", icon="✅")
            st.rerun()
        else:
            st.toast("Không tìm thấy lớp nào khớp với từ khóa!", icon="⚠️")
    
st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)

# ==========================================
# 2. PHẦN HIỂN THỊ VÀ CẬP NHẬT (ĐÃ ĐƯA LÊN TRÊN CÙNG)
# ==========================================
final_selected_id = st.session_state.get("selected_class_id")
class_info = class_options.get(final_selected_id)

if class_info:
    # NẾU ĐÃ TÌM THẤY LỚP -> HIỆN FORM SỬA LUÔN (KHÔNG HIỆN READ-ONLY NỮA)
    c1, c2, c3, c4 = st.columns([2, 2, 1.5, 2.5])
    
    # Logic tìm index cho selectbox
    try:
        curr_mj = class_info.get("MajorID")
        idx_mj = list(major_dict.keys()).index(curr_mj) if curr_mj in major_dict else 0
    except: idx_mj = 0
    
    try:
        curr_type = class_info.get("TypeID")
        idx_type = list(type_dict.keys()).index(curr_type) if curr_type in type_dict else 0
    except: idx_type = 0

    with c1:
        # Selectbox để chọn Ngành
        major_id = st.selectbox("Chuyên ngành", options=list(major_dict.keys()), format_func=lambda x: major_dict.get(x, ""), index=idx_mj, key="update_major_top")
    with c2:
        # Selectbox để chọn Hệ
        type_id = st.selectbox("Hệ / Loại", options=list(type_dict.keys()), format_func=lambda x: type_dict.get(x, ""), index=idx_type, key="update_type_top")
    with c3:
        # Input để sửa Năm
        year = st.text_input("Năm học", value=str(class_info.get("DateStart", ""))[:4], key="year_update_top")
    with c4:
        # Input để sửa Tên lớp
        class_name = st.text_input("Tên lớp", value=class_info.get("ClassName", ""), key="update_classname_top")

else:
    # NẾU CHƯA CHỌN LỚP -> HIỆN BỘ LỌC NHƯ CŨ
    c1, c2, c3, c4 = st.columns([2, 2, 1.5, 2.5])
    with c1:
        major_id = st.selectbox("Chuyên ngành", options=[None]+list(major_dict.keys()), format_func=lambda x: major_dict.get(x, "Tất cả"), key="filter_major")
    with c2:
        type_id = st.selectbox("Hệ / Loại", options=[None]+list(type_dict.keys()), format_func=lambda x: type_dict.get(x, "Tất cả"), key="filter_type")
    with c3:
        year = st.text_input("Năm học", placeholder="VD: 2024", key="filter_year")
    with c4:
        filtered_classes = [c for c in class_list if (not major_id or c.get("MajorID") == major_id) and (not type_id or c.get("TypeID") == type_id) and (not year or str(c.get("DateStart","")).startswith(year))]
        class_name_dict = {c["ClassID"]: c["ClassName"] for c in filtered_classes}
        
        current_selection = st.session_state.selected_class_id
        index = 0
        if current_selection in class_name_dict:
            keys_list = list(class_name_dict.keys())
            index = keys_list.index(current_selection) + 1
        
        def on_class_change():
            st.session_state.selected_class_id = st.session_state.dropdown_class_id
            
        st.selectbox("Chọn lớp", options=[None]+list(class_name_dict.keys()), index=index if index < len(class_name_dict) + 1 else 0, format_func=lambda x: class_name_dict.get(x, "Chọn lớp..."), key="dropdown_class_id", on_change=on_class_change)

st.markdown('<div style="border-bottom: 1px solid #eee; margin: 20px 0;"></div>', unsafe_allow_html=True)

# ==========================================
# 3. THÔNG TIN CHI TIẾT (INFO)
# ==========================================
final_selected_id = st.session_state.get("selected_class_id")
class_info = class_options.get(final_selected_id)

st.markdown("### 📋 Thông tin chi tiết")
    
if class_info:
    ic1, ic2, ic3 = st.columns(3)
    
    v_shift = shift_dict.get(class_info.get("ShiftID"), "Chưa rõ")
    v_wday = "Chưa rõ"
    try:
        d_start = class_info.get("DateStart")
        if d_start:
            if isinstance(d_start, str): d_start = datetime.datetime.strptime(d_start, "%Y-%m-%d")
            v_wday = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ nhật"][d_start.weekday()]
    except: pass

    with ic1:
        st.text_input("Mã lớp (Gốc)", value=class_info.get("ClassName",""), disabled=True, key="info_code")
        st.text_input("Ca học", value=v_shift, disabled=True, key="info_shift")
    with ic2:
        st.text_input("Tên môn học", value=class_info.get("FullClassName",""), disabled=True, key="info_fullname")
        st.text_input("Thứ học", value=v_wday, disabled=True, key="info_weekday")
    with ic3:
        st.text_input("Học kỳ", value=class_info.get("Semester",""), disabled=True, key="info_semester")
        st.markdown('<div style="margin-top: 29px;"></div>', unsafe_allow_html=True)
        
        # NÚT VÀO LỚP
        if st.button("🚀 VÀO LỚP NGAY", key="start_btn", use_container_width=True):
            st.session_state["selected_class_id"] = class_info["ClassID"]
            st.session_state["selected_class_info"] = class_info
            st.switch_page("pages/dashboard.py")
else:
    st.info("👈 Vui lòng tìm kiếm hoặc chọn lớp từ danh sách ở trên để xem thông tin.")

st.markdown('<div style="text-align: center; margin-top: 40px; color: #666; font-size: 14px;">Không tìm thấy lớp?</div>', unsafe_allow_html=True)
if st.button("+ Tạo lớp mới", key="create_new_class", use_container_width=True):
    st.switch_page("pages/add_class.py")