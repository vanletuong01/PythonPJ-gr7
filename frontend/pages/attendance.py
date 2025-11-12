import streamlit as st
import cv2
import time
from datetime import datetime
import os
import sys
from pathlib import Path

# ===============================
# 0️⃣ Cấu hình Path và Import
# ===============================
# Thêm thư mục gốc của dự án (D:\PythonPJ) vào sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import header
from frontend.components.header import render_header

# ===============================
# 1️⃣ Cấu hình trang
# ===============================
st.set_page_config(page_title="Điểm danh lớp học", layout="wide")
render_header()

# ===============================
# 2️⃣ Thư mục & trạng thái
# ===============================
SAVE_DIR = "uploads/attendance_images"
REGISTER_DIR = "uploads/student_registered"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(REGISTER_DIR, exist_ok=True)

if "camera_on" not in st.session_state:
    st.session_state.camera_on = False
if "attendance_done" not in st.session_state:
    st.session_state.attendance_done = False
if "captured_img" not in st.session_state:
    st.session_state.captured_img = None
if "recognition_data" not in st.session_state:
    st.session_state.recognition_data = {"name": None, "match_score": None}

# ===============================
# 3️⃣ Giao diện tiêu đề
# ===============================
st.markdown(
    """
    <h1 style='text-align:center; color:red; font-weight:bold; margin-top:10px;'>
        ĐIỂM DANH LỚP HỌC
    </h1>
    """,
    unsafe_allow_html=True,
)

# ===============================
# 4️⃣ Bố cục chính
# ===============================
left_col, right_col = st.columns([2.5, 1])

# ---- CỘT TRÁI: thông tin buổi, ngày, VÀ CAMERA STREAM ----
with left_col:
    st.markdown(
        """
        <div style='background-color:#ddd; padding:10px; border-radius:8px;'>
            <b>Buổi:</b> ____ &nbsp;&nbsp;&nbsp;&nbsp;
            <b>Ngày:</b> ____
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Placeholder 1: Camera Stream
    frame_placeholder = st.empty()

    # Placeholder 2: Kết quả nhận diện
    info_placeholder = st.empty()

    if not st.session_state.camera_on:
        frame_placeholder.markdown(
            """
            <div style='height:420px; border:2px solid #ccc; border-radius:8px; 
                        margin-top:8px; background:white; display:flex; 
                        align-items:center; justify-content:center; color:#888;'>
                Luồng camera sẽ hiển thị ở đây. Nhấn "Mở Camera" để bắt đầu.
            </div>
            """, unsafe_allow_html=True)
        # Hiển thị trạng thái chờ ở placeholder info
        info_placeholder.markdown(
            """
            <p style='text-align:center; font-size:18px; color:#555; margin-top:10px;'>
                Trạng thái: Đang chờ...
            </p>
            """, unsafe_allow_html=True)

# ---- CỘT PHẢI: ảnh và điều khiển camera ----
with right_col:
    # Đồng hồ
    current_time = datetime.now().strftime("%H:%M:%S %a, %d/%m/%Y")
    st.markdown(
        f"""
        <div style='border:1px solid #333; border-radius:8px; padding:6px; 
                    text-align:center; font-weight:bold; font-size:15px; width:220px; margin:auto;'>
            {current_time}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-weight:bold;'>ẢNH ĐÃ LƯU (Ảnh mẫu)</p>", unsafe_allow_html=True)

    # Ảnh đã lưu (mock)
    st.markdown("<div style='height:120px; background:#a00; border-radius:4px;'></div>", unsafe_allow_html=True)

    st.markdown("<br><p style='text-align:center; font-weight:bold;'>ẢNH HÔM NAY (Sau khi chụp)</p>",
                unsafe_allow_html=True)

    # Hiển thị ảnh sau khi chụp
    if st.session_state.captured_img is not None:
        try:
            st.image(st.session_state.captured_img, use_column_width=True)
        except Exception as e:
            st.warning(f"Không thể hiển thị ảnh. Lỗi: {e}")
    else:
        st.markdown("<div style='height:120px; background:#eee; border-radius:4px;'></div>", unsafe_allow_html=True)

    # Nút điều khiển camera
    st.markdown("<br>", unsafe_allow_html=True)
    if not st.session_state.camera_on:
        if st.button("📸 Mở Camera Điểm danh", use_container_width=True):
            st.session_state.camera_on = True
            st.session_state.attendance_done = False
            # Reset dữ liệu nhận diện khi bắt đầu
            st.session_state.recognition_data = {"name": None, "match_score": None}
            st.experimental_rerun()
    else:
        if st.button("🛑 Tắt Camera", use_container_width=True, type="primary"):
            st.session_state.camera_on = False
            st.experimental_rerun()

# ===============================
# 5️⃣ Xử lý LUỒNG VIDEO (STREAM) và NHẬN DIỆN
# ===============================
if st.session_state.camera_on:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("❌ Không thể mở camera. Vui lòng kiểm tra quyền truy cập.")
    else:
        st.info("ℹ️ Camera đang chạy. Đang tìm kiếm khuôn mặt...")

        # Đặt lại state nhận diện khi bắt đầu loop
        st.session_state.recognition_data = {"name": None, "match_score": None}

        # Biến đếm frame để không nhận diện quá nhanh (giúp giảm tải CPU)
        frame_count = 0

        while st.session_state.camera_on:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Chỉ chạy nhận diện 1 lần mỗi 5 frame
            if frame_count % 5 == 0:

                # ----------------------------------------------------
                # ❗️ GỌI HÀM NHẬN DIỆN CỦA BẠN TẠI ĐÂY ❗️
                # (student_id, confidence, box_coords) = recognize(frame)
                # ----------------------------------------------------

                # --- Giả lập (Mock) ---
                student_id = None

                # Giả lập: "nhận diện" được sau 3 giây (để dễ nhìn thấy)
                if 'start_time' not in st.session_state:
                    st.session_state.start_time = time.time()

                if time.time() - st.session_state.start_time > 3:
                    student_id = "Lê Văn Tùng"  # GIẢ LẬP ĐÃ TÌM THẤY
                    match_score = 92.5  # Giả lập độ chính xác
                    box_coords = (100, 50, 250, 300)  # (x1, y1, x2, y2)

                    st.session_state.recognition_data = {
                        "name": student_id,
                        "match_score": match_score
                    }

                    # Vẽ hộp màu xanh lá cây khi nhận diện được
                    cv2.rectangle(frame_rgb, box_coords[:2], box_coords[2:], (0, 255, 0), 2)
                else:
                    # Nếu chưa tìm thấy, hiển thị trạng thái tìm kiếm
                    st.session_state.recognition_data = {"name": None, "match_score": None}

                # Cập nhật kết quả nhận diện (Placeholder 2)
                if st.session_state.recognition_data["name"]:
                    info_placeholder.markdown(
                        f"""
                        <div style='text-align:center; padding:10px; border-radius:5px; background-color:#d4edda; color:#155724; font-weight:bold; margin-top:10px;'>
                            👤 **ĐÃ NHẬN DIỆN!**
                            <br>Tên: {st.session_state.recognition_data["name"]}
                            <br>Độ chính xác: {st.session_state.recognition_data["match_score"]:.2f}%
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    info_placeholder.markdown(
                        """
                        <p style='text-align:center; font-size:18px; color:#555; margin-top:10px;'>
                            Trạng thái: 🔍 Đang quét khuôn mặt...
                        </p>
                        """, unsafe_allow_html=True)

            # Hiển thị frame lên Placeholder 1
            frame_placeholder.image(frame_rgb, use_column_width=True)

            # Logic Chụp Ảnh và Dừng Camera (Chỉ chạy khi nhận diện thành công)
            if st.session_state.recognition_data["name"] is not None and not st.session_state.attendance_done:
                # TÌM THẤY! Chụp ảnh, lưu DB, và dừng.
                st.success(f"✅ Nhận diện thành công: {st.session_state.recognition_data['name']}. Đang lưu ảnh...")

                # 1. Chuẩn hóa tên file (Loại bỏ khoảng trắng/ký tự đặc biệt)
                # Thay thế các ký tự không an toàn cho tên file
                student_id_clean = "".join(
                    c if c.isalnum() or c in ('_', '-') else '_' for c in st.session_state.recognition_data['name'])

                # 2. Tạo đường dẫn thô
                img_name = f"attendance_{student_id_clean}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                img_path_raw = os.path.join(SAVE_DIR, img_name)

                # 3. Ghi file ảnh gốc (CV2 dùng đường dẫn gốc)
                success = cv2.imwrite(img_path_raw, frame)

                if success:
                    # 4. CHUẨN HÓA ĐƯỜNG DẪN cho Streamlit (dùng /)
                    img_path_clean = Path(img_path_raw).as_posix()

                    # Cập nhật state
                    st.session_state.captured_img = img_path_clean
                    st.session_state.attendance_done = True
                    st.session_state.camera_on = False
                    del st.session_state.start_time
                    st.balloons()
                else:
                    st.error(f"❌ Lỗi: Không thể ghi file ảnh vào ổ đĩa tại {img_path_raw}.")

            frame_count += 1
            time.sleep(0.01)  # Delay nhỏ

    cap.release()
    if not st.session_state.camera_on:
        st.experimental_rerun()