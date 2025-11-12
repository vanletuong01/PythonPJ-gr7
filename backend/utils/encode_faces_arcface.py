import os
import cv2
import time
import pickle
import numpy as np
import onnxruntime as ort
from collections import deque

# ✅ Import các module riêng
from models.face_module import extract_face_region, BlinkDetector
from utils.fake_detector import analyze_image as analyze_fake

# =========================
# ⚙️ CẤU HÌNH CHUNG
# =========================
MODEL_PATH = "models/face_encodings_arcface.pkl"
ARCFACE_ONNX = os.path.join("face_threshold_arcface", "buffalo_l", "w600k_r50.onnx")

THRESHOLD_RECOG = 0.65       # Ngưỡng nhận diện danh tính
THRESHOLD_FAKE_FINAL = 0.6   # Ngưỡng tin cậy real/fake
FPS_EST = 10                 # Ước lượng khung hình/giây

# =========================
# 🧠 LOAD MODEL VÀ DỮ LIỆU
# =========================
if not os.path.exists(ARCFACE_ONNX):
    print(f"❌ Không tìm thấy model ArcFace ONNX tại: {ARCFACE_ONNX}")
    exit()

print("🔹 Đang tải model ArcFace ONNX...")
arcface_sess = ort.InferenceSession(ARCFACE_ONNX, providers=["CPUExecutionProvider"])
arcface_input = arcface_sess.get_inputs()[0].name
print("✅ Model ArcFace ONNX đã sẵn sàng.")

if not os.path.exists(MODEL_PATH):
    print(f"❌ Không tìm thấy dữ liệu khuôn mặt: {MODEL_PATH}")
    exit()

with open(MODEL_PATH, "rb") as f:
    known_faces = pickle.load(f)
print(f"✅ Đã load {len(known_faces['names'])} khuôn mặt trong CSDL.")

# =========================
# 🧩 HÀM XỬ LÝ ẢNH
# =========================
def preprocess_arcface(img):
    """Chuẩn hóa ảnh đầu vào cho ArcFace"""
    img = cv2.resize(img, (112, 112))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = (img - 0.5) / 0.5
    img = np.transpose(img, (2, 0, 1))  # HWC → CHW
    return np.expand_dims(img, axis=0)

def get_embedding_arcface(face_img):
    """Trích xuất embedding 512 chiều từ khuôn mặt"""
    input_blob = preprocess_arcface(face_img)
    emb = arcface_sess.run(None, {arcface_input: input_blob})[0]
    emb = emb.flatten()
    emb /= np.linalg.norm(emb) + 1e-9
    return emb

# =========================
# 📱 PHÁT HIỆN VIỀN MÀN HÌNH
# =========================
def detect_border_smart(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 150)

    h, w = edges.shape
    border_mask = np.zeros_like(edges)
    border_w = int(0.08 * min(h, w))
    border_mask[:border_w, :] = 1
    border_mask[-border_w:, :] = 1
    border_mask[:, :border_w] = 1
    border_mask[:, -border_w:] = 1

    edge_density = np.sum(edges * border_mask) / (np.sum(border_mask) + 1e-9)
    border_brightness = np.mean(gray * border_mask)
    return edge_density > 25 or border_brightness > 180

# =========================
# 🤖 KẾT HỢP CÁC TÍN HIỆU
# =========================
def fuse_scores(fake_score_percent, blink_count, emb_var, border_flag, no_blink_flag):
    fake_p = np.clip(1.0 - fake_score_percent / 100.0, 0.0, 1.0)
    blink_penalty = 0.5 if blink_count == 0 else 0.0
    emb_penalty = np.clip((emb_var - 0.001) * 200.0, 0.0, 0.9)
    border_penalty = 0.8 if border_flag else 0.0
    no_blink_penalty = 1.0 if no_blink_flag else 0.0

    fake_belief = (
        0.5 * fake_p +
        0.2 * emb_penalty +
        0.15 * blink_penalty +
        0.1 * border_penalty +
        0.05 * no_blink_penalty
    )
    return np.clip(1.0 - fake_belief, 0.0, 1.0)

# =========================
# 📸 CHẠY ĐIỂM DANH
# =========================
def run_smart_attendance(duration=0):
    from facenet_pytorch import MTCNN
    mtcnn = MTCNN(image_size=112, margin=10, keep_all=True)
    blink_detector = BlinkDetector(window_s=6, fps_est=FPS_EST)

    cap = cv2.VideoCapture(0)
    print("📷 Mở webcam... (nhấn Q để thoát)")

    window_fake_scores = deque(maxlen=30)
    window_emb_dists = deque(maxlen=8)
    attended_names = set()
    fake_score_ema = None
    last_blink_time = time.time()
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes, _ = mtcnn.detect(rgb)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if boxes is None:
            cv2.putText(frame, "Không phát hiện khuôn mặt", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 200), 2)
        else:
            border_flag = detect_border_smart(frame)

            for box in boxes:
                x1, y1, x2, y2 = [int(v) for v in box]
                face_crop = extract_face_region(rgb, box)
                if face_crop is None:
                    continue

                # --- Nhận diện ---
                emb = get_embedding_arcface(face_crop)
                dists = np.linalg.norm(np.array(known_faces["encodings"]) - emb, axis=1)
                min_idx = int(np.argmin(dists))
                min_dist = float(np.min(dists))
                window_emb_dists.append(min_dist)
                avg_dist = np.mean(list(window_emb_dists))
                name = known_faces["names"][min_idx] if avg_dist < THRESHOLD_RECOG else "Unknown"

                # --- Phát hiện deepfake ---
                label_fake, fake_score = analyze_fake(face_crop)
                window_fake_scores.append(fake_score)

                if fake_score_ema is None:
                    fake_score_ema = fake_score / 100.0
                else:
                    alpha = 0.2
                    fake_score_ema = alpha * (fake_score / 100.0) + (1 - alpha) * fake_score_ema

                # --- Chớp mắt ---
                blink_count = blink_detector.update(gray, box)
                if blink_count > 0:
                    last_blink_time = time.time()

                no_blink_flag = (time.time() - last_blink_time) > 7
                emb_var = np.var(list(window_emb_dists)) if len(window_emb_dists) >= 2 else 0.0

                real_conf = fuse_scores(fake_score, blink_count, emb_var, border_flag, no_blink_flag)
                is_real = real_conf > THRESHOLD_FAKE_FINAL

                color = (0, 255, 0) if is_real else (0, 0, 255)
                status = f"{name} | {'REAL' if is_real else 'FAKE'} ({real_conf:.2f})"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, status, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                if border_flag:
                    cv2.rectangle(frame, (10, 10), (frame.shape[1]-10, frame.shape[0]-10),
                                  (0, 0, 255), 2)
                    cv2.putText(frame, "⚠️ NGHI NGO: VIỀN MÀN HÌNH", (30, frame.shape[0]-30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if is_real and name != "Unknown":
                    attended_names.add(name)

        cv2.imshow("🎯 Smart Face Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if duration > 0 and (time.time() - start_time) > duration:
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\n✅ Danh sách đã điểm danh:")
    for n in attended_names:
        print(" -", n)

# =========================
# ▶️ CHẠY CHÍNH
# =========================
if __name__ == "__main__":
    run_smart_attendance()
