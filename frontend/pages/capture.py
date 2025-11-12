# frontend/capture_ui.py
import streamlit as st
import cv2, time, os, datetime
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN
import requests
import sys

# ==========================================================
# ⚙️ 1. Cấu hình Streamlit (PHẢI nằm đầu tiên)
# ==========================================================
st.set_page_config(page_title="Lấy ảnh sinh viên", layout="wide")

# ==========================================================
# 🧭 2. Thiết lập đường dẫn
# ==========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(CURRENT_DIR, "..", "public", "images", "logo.png")

# Thêm đường dẫn gốc dự án để import backend nếu cần
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(BASE_DIR)

# ==========================================================
# 💅 3. Giao diện CSS
# ==========================================================
st.markdown("""
<style>
  header, footer {visibility: hidden;}
  .title { color:#d80000; font-size:28px; font-weight:700; margin-bottom:6px;}
  .gray-box {background:#e9e9e9;border-radius:8px;padding:12px;}
  .camera-frame {background:white;border:6px solid #bfcbd6;border-radius:6px;height:360px;display:flex;align-items:center;justify-content:center;}
  .info-count {font-size:18px;font-weight:700;text-align:center;margin-bottom:8px;color:#333;}
  .right-panel {display:flex;flex-direction:column;gap:12px;align-items:center;}
  .stButton>button {width:160px;height:44px;border-radius:8px;font-weight:700;}
  .clock {font-size:14px;color:#333;text-align:right;padding-right:8px;}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 🏫 4. Header
# ==========================================================
col_logo, col_title, col_clock = st.columns([1, 3, 1])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
    else:
        st.warning("Không tìm thấy logo.")
with col_title:
    st.markdown("<h4 style='margin:0;'>VIETNAM AVIATION ACADEMY</h4>", unsafe_allow_html=True)
    st.markdown("<div class='title'>LẤY ẢNH SINH VIÊN</div>", unsafe_allow_html=True)
with col_clock:
    st.markdown(f"<div class='clock'>{datetime.datetime.now().strftime('%H:%M:%S %a, %d/%m/%Y')}</div>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================================
# 🧾 5. Input thông tin sinh viên
# ==========================================================
col_mssv, col_name = st.columns([1, 3])
mssv = col_mssv.text_input("MSSV :", placeholder="Mã số sinh viên")
name = col_name.text_input("HỌ VÀ TÊN :", placeholder="Họ và tên")

# ==========================================================
# 🎥 6. Layout chính
# ==========================================================
left_col, right_col = st.columns([3, 1])
cam_ph = left_col.empty()
info_ph = left_col.empty()

with right_col:
    start_btn = st.button("Bật camera")
    stop_btn = st.button("Tắt camera")

output_dir = os.path.join(CURRENT_DIR, "..", "uploads", "face")
os.makedirs(output_dir, exist_ok=True)
directions = ["Nhìn thẳng", "Quay trái", "Quay phải", "Ngẩng đầu", "Cúi xuống"]

# ==========================================================
# 🧠 7. Session State
# ==========================================================
st.session_state.setdefault("capturing", False)
st.session_state.setdefault("photo_count", 0)
st.session_state.setdefault("max_photos", 25)
st.session_state.setdefault("current_dir", 0)

# ==========================================================
# 🧩 8. MTCNN Detector
# ==========================================================
@st.cache_resource
def get_mtcnn():
    return MTCNN(keep_all=True, post_process=False, min_face_size=60)

detector = get_mtcnn()

# ==========================================================
# 🔧 9. Xử lý ảnh
# ==========================================================
def adjust_lighting(img):
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    balanced = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    gamma = np.random.uniform(0.8, 1.4)
    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(balanced, table)

def denoise_and_sharpen(img):
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(denoised, -1, sharpen_kernel)

def preprocess_face(img, box):
    x1, y1, x2, y2 = [int(b) for b in box]
    face = img[y1:y2, x1:x2]
    if face.size == 0:
        return None
    face = cv2.resize(face, (112, 112))
    face = adjust_lighting(face)
    face = denoise_and_sharpen(face)
    return face

# ==========================================================
# ☁️ 10. Upload ảnh lên backend
# ==========================================================
def upload_images_to_backend(student_code, full_name, images_folder, backend_url="http://127.0.0.1:8000"):
    register_url = backend_url.rstrip("/") + "/api/face/register"
    finalize_url = backend_url.rstrip("/") + "/api/face/finalize"

    if not os.path.exists(images_folder):
        return {"success": False, "message": "Folder ảnh không tồn tại"}

    files = [f for f in sorted(os.listdir(images_folder)) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return {"success": False, "message": "Không có ảnh để upload"}

    session = requests.Session()
    for idx, fname in enumerate(files, start=1):
        path = os.path.join(images_folder, fname)
        try:
            with open(path, "rb") as fh:
                files_payload = {"photo": (fname, fh, "image/jpeg")}
                data = {"student_code": student_code, "full_name": full_name, "index": idx}
                resp = session.post(register_url, data=data, files=files_payload, timeout=30)
                if resp.status_code not in (200, 201):
                    print(f"⚠️ Upload {fname} trả về {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Lỗi upload {fname}: {e}")

    try:
        resp = session.get(finalize_url, params={"student_code": student_code, "full_name": full_name}, timeout=60)
        if resp.status_code == 200:
            return {"success": True, "message": "Finalize thành công", "detail": resp.json()}
        else:
            return {"success": False, "message": f"Finalize trả về {resp.status_code}", "detail": resp.text}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==========================================================
# 📸 11. Capture Logic
# ==========================================================
if start_btn:
    st.session_state.capturing = True
    st.session_state.photo_count = 0

if stop_btn:
    st.session_state.capturing = False

if st.session_state.capturing:
    cap = cv2.VideoCapture(0)
    time.sleep(0.3)
    try:
        while st.session_state.capturing and st.session_state.photo_count < st.session_state.max_photos:
            ret, frame = cap.read()
            if not ret:
                info_ph.markdown("<div class='info-count'>Không lấy được hình từ camera</div>", unsafe_allow_html=True)
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(rgb)
            boxes, probs = detector.detect(img_pil)

            guide = f"Hướng dẫn: {directions[st.session_state.current_dir]}"
            if boxes is not None and len(boxes) > 0:
                box = boxes[np.argmax(probs)]
                face_img = preprocess_face(frame, box)
                if face_img is not None:
                    student_dir = os.path.join(output_dir, mssv or "unknown")
                    os.makedirs(student_dir, exist_ok=True)
                    filename = f"{mssv}_{st.session_state.photo_count + 1}.jpg"
                    cv2.imwrite(os.path.join(student_dir, filename), face_img)
                    st.session_state.photo_count += 1
                    info_ph.markdown(f"<div class='info-count'>Đã chụp {st.session_state.photo_count}/{st.session_state.max_photos}</div>", unsafe_allow_html=True)

                    if st.session_state.photo_count % 5 == 0 and st.session_state.current_dir < len(directions) - 1:
                        st.session_state.current_dir += 1
                    time.sleep(1)
            cam_ph.image(rgb, use_column_width=True)

        cap.release()
        if st.session_state.photo_count >= st.session_state.max_photos:
            st.success(f"✅ Hoàn tất chụp ảnh cho {mssv}. Đang upload ảnh lên backend & sinh embedding...")
            st.session_state.capturing = False
            st.session_state.current_dir = 0
            folder = os.path.join(output_dir, mssv or "unknown")
            res = upload_images_to_backend(mssv or "unknown", name or "", folder)
            if res.get("success"):
                st.success("Upload và finalize thành công.")
            else:
                st.error(f"Lỗi khi upload/finalize: {res.get('message')}")
    except Exception as e:
        st.error(f"Lỗi camera: {e}")

else:
    cam_ph.markdown("<div class='camera-frame'></div>", unsafe_allow_html=True)
    info_ph.markdown(f"<div class='info-count'>Đã chụp {st.session_state.photo_count}/{st.session_state.max_photos}</div>", unsafe_allow_html=True)

# ==========================================================
# 🧹 12. Footer
# ==========================================================
st.markdown("---")
if st.button("Reset"):
    st.session_state.photo_count = 0
    st.session_state.current_dir = 0
    st.success("Đã reset.")
