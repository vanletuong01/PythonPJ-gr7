import streamlit as st
from components.sidebar_auth import render_auth_sidebar
from services.api_client import get_majors, get_types, get_classes_by_teacher, get_shifts

if not st.session_state.get("logged_in", False) or not st.session_state.get("teacher", {}).get("id_login"):
    st.warning("Bạn cần đăng nhập để vào lớp.")
    st.switch_page("app.py")
    st.stop()

st.set_page_config(page_title="Vào lớp", layout="wide")

# Sidebar trái
col_left, col_right = st.columns([1.2, 2])

with col_left:
    render_auth_sidebar()

with col_right:
    st.markdown("<h2 style='margin:0'>VÀO LỚP</h2>", unsafe_allow_html=True)

    # Kiểm tra đăng nhập
    teacher = st.session_state.get("teacher")
    if not teacher or not teacher.get("id_login"):
        st.warning("Bạn cần đăng nhập để vào lớp.")
        st.stop()
    id_login = teacher["id_login"]
    # Lấy dữ liệu filter
    majors = get_majors() or []
    types = get_types() or []
    shifts = get_shifts() or []
    major_dict = {m['MajorID']: m['MajorName'] for m in majors}
    type_dict = {t['TypeID']: t['TypeName'] for t in types}
    shift_dict = {s['ShiftID']: s['ShiftName'] for s in shifts}

    # Lấy danh sách lớp của giáo viên
    class_list = get_classes_by_teacher(id_login) or []
    # Tạo dict để tra cứu nhanh
    class_options = {c["ClassID"]: c for c in class_list}

    # Bộ lọc
    col_major, col_type, col_year, col_class = st.columns([2,2,1,3])
    with col_major:
        major_id = st.selectbox("Chọn chuyên ngành", options=[None]+list(major_dict.keys()), format_func=lambda x: major_dict.get(x, "—") if x else "—")
    with col_type:
        type_id = st.selectbox("Chọn loại", options=[None]+list(type_dict.keys()), format_func=lambda x: type_dict.get(x, "—") if x else "—")
    with col_year:
        year = st.text_input("Chọn năm học", value="", placeholder="2025")
    with col_class:
        # Lọc lớp theo các filter trên
        filtered_classes = [
            c for c in class_list
            if (not major_id or c["MajorID"] == major_id)
            and (not type_id or c["TypeID"] == type_id)
            and (not year or str(c["DateStart"]).startswith(year))
        ]
        class_name_dict = {c["ClassID"]: c["ClassName"] for c in filtered_classes}
        selected_class_id = st.selectbox("Chọn lớp của bạn", options=[None]+list(class_name_dict.keys()), format_func=lambda x: class_name_dict.get(x, "—") if x else "—")

    # Tìm kiếm theo mã lớp, tên lớp, tên môn học
    col_code, col_search = st.columns([3,1])
    with col_code:
        search_text = st.text_input("Mã lớp / Tên lớp / Tên môn học:", value="", placeholder="Nhập để tìm kiếm")
    with col_search:
        if st.button("Tìm"):
            # Ưu tiên tìm theo mã lớp (ClassName), nếu không thì tìm theo FullClassName hoặc CourseCode
            found = None
            for c in class_list:
                if (search_text.lower() in str(c["ClassName"]).lower() or
                    search_text.lower() in str(c.get("FullClassName", "")).lower() or
                    search_text.lower() in str(c.get("CourseCode", "")).lower() or
                    search_text.lower() in str(c.get("Session", "")).lower()):
                    found = c
                    break
            if found:
                selected_class_id = found["ClassID"]
                st.session_state["selected_class_id"] = selected_class_id
            else:
                st.warning("Không tìm thấy lớp phù hợp.")

    # Nếu vừa tìm kiếm thì ưu tiên hiển thị lớp đó
    selected_class_id = st.session_state.get("selected_class_id", selected_class_id)

    # Hiển thị thông tin lớp đã chọn
    class_info = class_options.get(selected_class_id)
    if class_info:
        st.text_input("Mã lớp:", value=class_info["ClassName"], disabled=True)
        st.text_input("Tên môn học:", value=class_info.get("Session", ""), disabled=True)
        st.text_input("Học kỳ:", value=class_info.get("Semester", ""), disabled=True)
        shift_name = shift_dict.get(class_info.get("ShiftID"), "")
        st.text_input("Ca học:", value=shift_name, disabled=True)
        # Tính thứ học từ DateStart
        import datetime
        try:
            date_start = class_info.get("DateStart")
            weekday = ""
            if date_start:
                if isinstance(date_start, str):
                    date_start = datetime.datetime.strptime(date_start, "%Y-%m-%d")
                weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
                weekday = weekdays[date_start.weekday()]
            st.text_input("Thứ học:", value=weekday, disabled=True)
        except Exception:
            st.text_input("Thứ học:", value="", disabled=True)
    else:
        st.text_input("Mã lớp:", value="", disabled=True)
        st.text_input("Tên môn học:", value="", disabled=True)
        st.text_input("Học kỳ:", value="", disabled=True)
        st.text_input("Ca học:", value="", disabled=True)
        st.text_input("Thứ học:", value="", disabled=True)

    if class_info and st.button("START", use_container_width=True):
<<<<<<< HEAD
        st.session_state["selected_class_id"] = class_info["ClassID"] 
        st.success(f"Bạn đã vào lớp {class_info['ClassName']} thành công!")
        st.switch_page("pages/dashboard.py")
=======
        st.session_state["selected_class_id"] = class_info["ClassID"]
        st.success(f"Bạn đã vào lớp {class_info['ClassName']} thành công!")
        st.switch_page("pages/dashboard.py")        
>>>>>>> e660665db4b78d84c712b369d61b71444ed75c46
    st.markdown(
        '<div style="margin-top:10px;font-size:14px;color:#666">Bạn không tìm thấy lớp của mình? <a href="/add_class" style="color:#d00;font-weight:600">Tại đây</a>.</div>',
        unsafe_allow_html=True
    )