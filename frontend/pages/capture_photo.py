import streamlit as st
import requests
from pathlib import Path
import sys
from backend.app.services.capture_service import save_images_and_generate_embedding

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from components.capture_component import capture_component

st.set_page_config(
    page_title="Capture 25 Photos",
    layout="wide",  # ← Đổi từ "centered" sang "wide"
    initial_sidebar_state="collapsed"
)

# Load CSS
css_path = Path(__file__).parent.parent / "public" / "css" / "capture_photo.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ===== TITLE =====
st.markdown("<h1 style='text-align:center; color:white;'>📸 Chụp tự động 25 ảnh sinh viên</h1>", unsafe_allow_html=True)

# ===== STUDENT INFO =====
student_code = st.query_params.get("code", "") or st.session_state.get("capture_mssv", "")
full_name = st.query_params.get("name", "") or st.session_state.get("capture_name", "")

if not student_code or not full_name:
    st.error("❌ Thiếu MSSV hoặc Họ tên")
    if st.button("⬅ Quay lại"):
        st.switch_page("pages/add_student.py")
    st.stop()

st.markdown(
    f"<div style='background:white; padding:12px 24px; border-radius:12px; text-align:center; "
    f"font-size:16px; font-weight:600; max-width:500px; margin:0 auto 1.5rem; box-shadow:0 4px 12px rgba(0,0,0,0.15);'>"
    f"<span style='color:#667eea;'>MSSV:</span> {student_code} &nbsp;│&nbsp; "
    f"<span style='color:#667eea;'>Họ tên:</span> {full_name}"
    f"</div>",
    unsafe_allow_html=True
)

# ===== STATE =====
st.session_state.setdefault("photos", [])
st.session_state.setdefault("capturing", False)
st.session_state.setdefault("photo_set", set())

# ===== PROGRESS BAR =====
if st.session_state.capturing or len(st.session_state.photos) > 0:
    current = len(st.session_state.photos)
    progress = current / 25
    
    if st.session_state.capturing:
        st.info(f"📸 Đang chụp: {current}/25")
    elif current >= 25:
        st.success(f"✅ Hoàn tất: {current}/25")
    else:
        st.warning(f"⚠️ Đã chụp: {current}/25")
    
    st.progress(progress)

st.write("")  # Spacing

# ===== BUTTONS =====
col1, col2, col3 = st.columns(3)

with col1:
    if not st.session_state.capturing and len(st.session_state.photos) < 25:
        start_btn = st.button("🚀 Bắt đầu chụp", type="primary", use_container_width=True, key="start_btn")
        if start_btn:
            st.session_state.photos = []
            st.session_state.photo_set = set()
            st.session_state.capturing = True
            st.rerun()
    else:
        # Placeholder khi đang chụp
        st.button("🚀 Bắt đầu chụp", disabled=True, use_container_width=True, key="start_disabled")

with col2:
    if len(st.session_state.photos) >= 25 and not st.session_state.capturing:
        send_btn = st.button("📤 Gửi backend", type="primary", use_container_width=True, key="send_btn")
        if send_btn:
            with st.spinner("⏳ Đang upload..."):
                payload = {
                    "student_code": student_code,
                    "full_name": full_name,
                    "images": st.session_state.photos[:25]
                }
                
                try:
                    res = requests.post(
                        "http://127.0.0.1:8000/api/v1/capture/save-face-images",
                        json=payload,
                        timeout=120
                    )
                    
                    if res.status_code == 200:
                        st.success("✅ Đã lưu thành công!")
                        data = res.json()
                        st.info(f"📁 {data.get('folder')}")
                        st.info(f"📊 {data.get('saved')}/25 ảnh")
                    else:
                        st.error(f"❌ Lỗi {res.status_code}")
                except Exception as e:
                    st.error(f"❌ {e}")
    else:
        st.button("📤 Gửi backend", disabled=True, use_container_width=True, key="send_disabled")

with col3:
    if len(st.session_state.photos) >= 25 and not st.session_state.capturing:
        retry_btn = st.button("🔄 Chụp lại", use_container_width=True, key="retry_btn")
        if retry_btn:
            st.session_state.photos = []
            st.session_state.photo_set = set()
            st.session_state.capturing = False
            st.rerun()
    else:
        st.button("🔄 Chụp lại", disabled=True, use_container_width=True, key="retry_disabled")

st.write("")  # Spacing

# ===== CAMERA COMPONENT =====
st.markdown("### 📹 Camera")

result = capture_component(
    start_capture=st.session_state.capturing,
    key="webcam"
)

# ===== RECEIVE IMAGES =====
if result and isinstance(result, dict):
    if result.get("status") == "done":
        st.session_state.capturing = False
        st.rerun()
    
    elif "image" in result and "index" in result:
        idx = result["index"]
        if idx not in st.session_state.photo_set:
            st.session_state.photo_set.add(idx)
            st.session_state.photos.append(result["image"])
            st.rerun()

# ===== IMAGE GRID =====
if len(st.session_state.photos) >= 25 and not st.session_state.capturing:
    st.markdown("---")
    st.markdown("### 📂 Ảnh đã chụp")
    
    cols = st.columns(5)
    for i, img in enumerate(st.session_state.photos[:25]):
        with cols[i % 5]:
            st.image(img, caption=f"#{i+1}", use_container_width=True)

if len(st.session_state.photos) >= 25 and not st.session_state.capturing:
    st.markdown("---")
    st.markdown("### 📂 Ảnh đã chụp")
    
    cols = st.columns(5)
    for i, img in enumerate(st.session_state.photos[:25]):
        with cols[i % 5]:
            st.image(img, caption=f"#{i+1}", use_container_width=True)

    # New code block starts here
    folder = f"captures/{student_code}"
    db = None  # Replace with actual db instance if available

    # Call the new function with the required parameters
    embedding_result = save_images_and_generate_embedding(
        student_id=stu.StudentID,
        student_code=payload.student_code,
        image_folder=folder,
        db=db
    )
    # New code block ends here
