import streamlit as st
from pathlib import Path
import datetime
from components.sidebar_auth import render_auth_sidebar
from services.api_client import get_majors, get_types, get_classes_by_teacher, get_shifts

# ==== PAGE CONFIG ====
st.set_page_config(page_title="Vào lớp", layout="wide")

# ==== LOAD CSS ====
css_path = Path(__file__).parent.parent / "public" / "css" / "join_class.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ==== CHECK LOGIN (giữ nguyên logic) ====
if not st.session_state.get("logged_in", False) or not st.session_state.get("teacher", {}).get("id_login"):
    st.warning("Bạn cần đăng nhập để vào lớp.")
    st.switch_page("app.py")
    st.stop()

# ==== LEFT - RIGHT LAYOUT ====
col_left, col_right = st.columns([1.2, 2], gap="large")

with col_left:
    # Wrap left area so CSS can target it if needed
    st.markdown('<div class="left-sidebar">', unsafe_allow_html=True)
    render_auth_sidebar()
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:

    # =============================
    #         TIÊU ĐỀ FIGMA
    # =============================
    st.markdown("""
        <div class="page-title" style="margin-top:-6px;">
            ← VÀO LỚP
        </div>
    """, unsafe_allow_html=True)

    teacher = st.session_state.get("teacher")
    id_login = teacher.get("id_login")

    # master data (giữ nguyên cách gọi API)
    majors = get_majors() or []
    types = get_types() or []
    shifts = get_shifts() or []

    major_dict = {m['MajorID']: m['MajorName'] for m in majors}
    type_dict = {t['TypeID']: t['TypeName'] for t in types}
    shift_dict = {s['ShiftID']: s['ShiftName'] for s in shifts}

    class_list = get_classes_by_teacher(id_login) or []
    class_options = {c["ClassID"]: c for c in class_list}

    # =============================
    #       HÀNG FILTER (FIGMA)
    # =============================
    st.markdown('<div class="css-filter-row" style="margin-top:8px;"></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2,2,1.4,2.4])

    with col1:
        major_id = st.selectbox(
            "Chuyên ngành",
            options=[None] + list(major_dict.keys()),
            format_func=lambda x: major_dict.get(x, "—") if x else "—"
        )

    with col2:
        type_id = st.selectbox(
            "Hệ / Loại",
            options=[None] + list(type_dict.keys()),
            format_func=lambda x: type_dict.get(x, "—") if x else "—"
        )

    with col3:
        year = st.text_input("Năm học", placeholder="2025")

    with col4:
        filtered_classes = [
            c for c in class_list
            if (not major_id or c["MajorID"] == major_id)
            and (not type_id or c["TypeID"] == type_id)
            and (not year or str(c.get("DateStart","")).startswith(year))
        ]
        class_name_dict = {c["ClassID"]: c["ClassName"] for c in filtered_classes}

        selected_class_id = st.selectbox(
            "Chọn lớp của bạn",
            options=[None] + list(class_name_dict.keys()),
            format_func=lambda x: class_name_dict.get(x, "—") if x else "—"
        )

    # =============================
    #           SEARCH BOX (FIGMA)
    # =============================
    st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)

    # container to control search input + button
    search_cols = st.columns([4,1])
    with search_cols[0]:
        search_text = st.text_input(
            "Mã lớp / Tên lớp / Tên môn học:",
            placeholder="Nhập để tìm kiếm"
        )
    with search_cols[1]:
        # Use use_container_width to make visually similar to Figma
        if st.button("Tìm", use_container_width=True):
            found = None
            q = (search_text or "").strip().lower()

            for c in class_list:
                if q and (
                    q in str(c.get("ClassName","")).lower()
                    or q in str(c.get("FullClassName","")).lower()
                    or q in str(c.get("CourseCode","")).lower()
                    or q in str(c.get("Session","")).lower()
                ):
                    found = c
                    break

            if found:
                st.session_state["selected_class_id"] = found["ClassID"]
                selected_class_id = found["ClassID"]
                st.success(f"Đã tìm thấy: {found.get('ClassName')}")
            else:
                st.warning("Không tìm thấy lớp phù hợp.")

    # preserve selected from previous searches
    selected_class_id = st.session_state.get("selected_class_id", selected_class_id)
    class_info = class_options.get(selected_class_id)

    # =============================
    #        CARD THÔNG TIN (FIGMA)
    # =============================
    st.markdown('<div class="class-card">', unsafe_allow_html=True)

    if class_info:
        st.text_input("Mã lớp:", value=class_info.get("ClassName",""), disabled=True)
        st.text_input("Tên môn học:", value=class_info.get("Session",""), disabled=True)
        st.text_input("Học kỳ:", value=class_info.get("Semester",""), disabled=True)

        shift_name = shift_dict.get(class_info.get("ShiftID"), "")
        st.text_input("Ca học:", value=shift_name, disabled=True)

        weekday = ""
        try:
            date_start = class_info.get("DateStart")
            if date_start:
                if isinstance(date_start, str):
                    date_start = datetime.datetime.strptime(date_start, "%Y-%m-%d")
                weekdays = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ nhật"]
                weekday = weekdays[date_start.weekday()]
        except Exception:
            weekday = ""

        st.text_input("Thứ học:", value=weekday, disabled=True)

    else:
        # placeholders (giữ biến tên giống bạn)
        st.text_input("Mã lớp:", "", disabled=True)
        st.text_input("Tên môn học:", "", disabled=True)
        st.text_input("Học kỳ:", "", disabled=True)
        st.text_input("Ca học:", "", disabled=True)
        st.text_input("Thứ học:", "", disabled=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # =============================
    #             START (giữ logic)
    # =============================
    if class_info and st.button("START", use_container_width=True, key="start_button"):
        st.session_state["selected_class_id"] = class_info["ClassID"]
        st.session_state["selected_class_info"] = class_info  # Lưu cả thông tin lớp
        st.success(f"Bạn đã vào lớp {class_info['ClassName']} thành công!")
        st.switch_page("pages/dashboard.py")
# ← trang bạn muốn chuyển đến



    # help link (giữ nguyên)
    st.markdown(
        '<div class="help-text">Bạn không tìm thấy lớp của mình? '
        '<a href="/add_class" style="color:#d00;font-weight:600">Tại đây</a>.</div>',
        unsafe_allow_html=True
    )

        # ====== LOAD CSS SAU CÙNG — QUAN TRỌNG NHẤT ======
    css_path = Path(__file__).parent.parent / "public" / "css" / "join_class.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)

