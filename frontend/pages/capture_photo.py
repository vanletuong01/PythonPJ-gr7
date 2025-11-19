import streamlit as st
import requests
from pathlib import Path
import sys

# ===== CẤU HÌNH TRANG =====
st.set_page_config(
    page_title="Chụp ảnh Training",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== IMPORT COMPONENTS =====
# Thêm đường dẫn gốc để import capture_component
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Giả sử bạn đã có component này (nếu chưa có thì dùng st.camera_input thay thế)
try:
    from components.capture_component import capture_component
except ImportError:
    # Fallback nếu không tìm thấy component
    capture_component = None

# ===== LOAD CSS =====
css_path = Path(__file__).parent.parent / "public" / "css" / "capture_photo.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
else:
    # CSS mặc định nếu file không tồn tại
    st.markdown("""
        <style>
            .block-container { padding-top: 20px !important; }
            .stProgress > div > div > div > div { background-color: #667eea; }
        </style>
    """, unsafe_allow_html=True)

# ===== LẤY DỮ LIỆU TỪ SESSION =====
# Ưu tiên lấy từ session state do trang trước (add_student/student_detail) gửi sang
student_code = st.session_state.get("capture_mssv", "")
full_name = st.session_state.get("capture_name", "")
prev_page = st.session_state.get("capture_prev_page", "pages/add_student.py")

# ===== NÚT QUAY LẠI (NAV BAR) =====
col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("⬅️ Quay lại", use_container_width=True):
        st.switch_page(prev_page)

# Kiểm tra dữ liệu đầu vào
if not student_code or not full_name:
    st.error("⚠️ Thiếu thông tin sinh viên (MSSV/Tên). Vui lòng quay lại chọn sinh viên.")
    st.stop()

# ===== GIAO DIỆN CHÍNH =====
st.markdown("<h2 style='text-align:center; margin-bottom: 10px;'>📸 Chụp 25 ảnh Training</h2>", unsafe_allow_html=True)

# Card thông tin sinh viên
st.markdown(
    f"""
    <div style='background:#f8f9fa; padding:15px; border-radius:10px; text-align:center; 
    border:1px solid #e9ecef; margin-bottom: 20px;'>
        <span style='font-weight:600; color:#555;'>Sinh viên:</span> 
        <span style='font-size:18px; font-weight:bold; color:#333;'>{full_name}</span> 
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style='font-weight:600; color:#555;'>MSSV:</span> 
        <span style='font-size:18px; font-weight:bold; color:#667eea;'>{student_code}</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ===== KHỞI TẠO STATE =====
if "photos" not in st.session_state:
    st.session_state.photos = []
if "capturing" not in st.session_state:
    st.session_state.capturing = False
if "photo_set" not in st.session_state:
    st.session_state.photo_set = set()

# ===== PROGRESS BAR =====
current_photos = len(st.session_state.photos)
progress = min(current_photos / 25, 1.0)

if current_photos > 0:
    st.progress(progress)
    if current_photos < 25:
        st.info(f"📷 Đã chụp: **{current_photos}/25** ảnh")
    else:
        st.success(f"✅ Đã đủ **{current_photos}/25** ảnh. Hãy nhấn 'Gửi Backend' để lưu.")

# ===== CONTROL BUTTONS =====
c1, c2, c3 = st.columns(3)

with c1:
    # Nút BẮT ĐẦU CHỤP
    if not st.session_state.capturing and current_photos < 25:
        if st.button("🚀 Bắt đầu chụp", type="primary", use_container_width=True):
            st.session_state.photos = []
            st.session_state.photo_set = set()
            st.session_state.capturing = True
            st.rerun()
    elif st.session_state.capturing:
        if st.button("⏹️ Dừng chụp", type="secondary", use_container_width=True):
            st.session_state.capturing = False
            st.rerun()
    else:
        st.button("🚀 Bắt đầu chụp", disabled=True, use_container_width=True)

with c2:
    # Nút GỬI BACKEND
    # Chỉ hiện khi đủ 25 ảnh và không đang chụp
    can_send = (current_photos >= 25 and not st.session_state.capturing)
    if st.button("📤 Gửi & Training", type="primary", use_container_width=True, disabled=not can_send):
        if can_send:
            with st.spinner("⏳ Đang gửi ảnh và training model..."):
                payload = {
                    "student_code": student_code,
                    "full_name": full_name,
                    "images": st.session_state.photos[:25] # Chỉ lấy đúng 25 ảnh
                }
                
                try:
                    # Gọi API Backend
                    # Lưu ý: Backend sẽ tự gọi logic save_images_and_generate_embedding
                    res = requests.post(
                        "http://127.0.0.1:8000/api/v1/capture/save-face-images",
                        json=payload,
                        timeout=120
                    )
                    
                    if res.status_code == 200:
                        st.balloons()
                        st.success("✅ Lưu ảnh và Training thành công!")
                        data = res.json()
                        st.toast(f"Đã lưu vào: {data.get('folder', 'Unknown')}")
                        
                        # Reset sau khi thành công
                        st.session_state.photos = []
                        st.session_state.photo_set = set()
                        
                        # Tự động quay về trang trước sau 2s (Optional)
                        # import time
                        # time.sleep(2)
                        # st.switch_page(prev_page)
                        
                    else:
                        st.error(f"❌ Lỗi từ Server: {res.status_code} - {res.text}")
                except Exception as e:
                    st.error(f"❌ Lỗi kết nối: {e}")

with c3:
    # Nút CHỤP LẠI
    if st.button("🔄 Reset / Chụp lại", use_container_width=True):
        st.session_state.photos = []
        st.session_state.photo_set = set()
        st.session_state.capturing = False
        st.rerun()

st.markdown("---")

# ===== CAMERA COMPONENT =====
# Logic: Sử dụng component custom để chụp tự động
if st.session_state.capturing:
    col_cam, col_guide = st.columns([2, 1])
    
    with col_cam:
        st.markdown("### 📹 Camera đang bật")
        if capture_component:
            # Component custom chụp ảnh liên tục
            result = capture_component(
                start_capture=st.session_state.capturing,
                key="webcam"
            )
            
            # Xử lý kết quả trả về từ JS Component
            if result and isinstance(result, dict):
                if result.get("status") == "done":
                    st.session_state.capturing = False
                    st.rerun()
                elif "image" in result and "index" in result:
                    idx = result["index"]
                    # Tránh chụp trùng lặp quá nhanh
                    if idx not in st.session_state.photo_set:
                        st.session_state.photo_set.add(idx)
                        st.session_state.photos.append(result["image"])
                        # Refresh lại UI để cập nhật thanh Progress
                        st.rerun()
        else:
            # Fallback nếu không có component: Dùng st.camera_input (Chụp thủ công)
            img_file = st.camera_input("Chụp thủ công (Do thiếu component)")
            if img_file:
                import base64
                bytes_data = img_file.getvalue()
                base64_str = "data:image/jpeg;base64," + base64.b64encode(bytes_data).decode()
                st.session_state.photos.append(base64_str)
                st.rerun()

    with col_guide:
        st.info("""
        **Hướng dẫn:**
        1. Giữ mặt ở chính giữa khung hình.
        2. Xoay nhẹ mặt sang trái/phải/lên/xuống.
        3. Hệ thống sẽ tự động chụp 25 tấm.
        4. Sau khi xong, nhấn **Gửi & Training**.
        """)

# ===== HIỂN THỊ ẢNH ĐÃ CHỤP (GRID) =====
if len(st.session_state.photos) > 0 and not st.session_state.capturing:
    st.markdown("### 📂 Ảnh đã chụp")
    
    # Hiển thị lưới 5 cột
    cols = st.columns(5)
    for i, img in enumerate(st.session_state.photos[:25]):
        with cols[i % 5]:
            st.image(img, caption=f"Ảnh {i+1}", use_container_width=True)