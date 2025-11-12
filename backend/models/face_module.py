# smart_face_attendance.py
import os
import cv2
import torch
import numpy as np
import pickle
from facenet_pytorch import MTCNN, InceptionResnetV1
from collections import deque
from PIL import Image
from face_app.fake_detector import analyze_image  # dùng fake detector có sẵn

# ===============================
# 1️⃣ Cấu hình và khởi tạo
# ===============================
MODEL_PATH = "models/face_encodings_arcface.pkl"
THRESHOLD = 0.65
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"🚀 Using device: {device}")

mtcnn = MTCNN(image_size=160, margin=20, keep_all=True, device=device)
arcface = InceptionResnetV1(pretrained='vggface2').eval().to(device)
_eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# ===============================
# 2️⃣ Blink Detector
# ===============================
class BlinkDetector:
    def __init__(self, window_s=8, fps_est=10):
        self.window_frames = int(window_s * fps_est)
        self.history = deque(maxlen=max(5, self.window_frames))
        self.last_eye_count = 0
        self.blink_count = 0

    def update(self, gray_frame, face_box=None):
        roi = gray_frame
        if face_box is not None:
            x1, y1, x2, y2 = [int(v) for v in face_box]
            h, w = gray_frame.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            roi = gray_frame[y1:int(y1 + (y2-y1)*0.45), x1:x2]
        eyes = _eye_cascade.detectMultiScale(roi, 1.1, 3, minSize=(8,8))
        eye_count = len(eyes)
        if self.last_eye_count > 0 and eye_count == 0:
            self.blink_count += 1
        self.last_eye_count = eye_count
        self.history.append(1 if self.blink_count > 0 else 0)
        return sum(self.history)

# ===============================
# 3️⃣ Hàm tiện ích
# ===============================
def extract_face_region(frame, box):
    x1, y1, x2, y2 = [int(v) for v in box]
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]

def embedding_from_face(face_rgb):
    """Trả về vector embedding (numpy) từ khuôn mặt RGB"""
    pil = Image.fromarray(face_rgb)
    face_tensor = mtcnn(pil, return_prob=False)
    if face_tensor is None:
        return None
    with torch.no_grad():
        emb = arcface(face_tensor.to(device)).detach().cpu().numpy()[0]
    return emb / (np.linalg.norm(emb) + 1e-8)

# ===============================
# 4️⃣ Load dữ liệu huấn luyện
# ===============================
if not os.path.exists(MODEL_PATH):
    print("❌ Chưa có dữ liệu train ArcFace. Chạy train_faces.py trước!")
    exit()
with open(MODEL_PATH, 'rb') as f:
    known_faces = pickle.load(f)
print(f"✅ Đã load {len(known_faces['names'])} khuôn mặt.")

# ===============================
# 5️⃣ Vòng lặp webcam
# ===============================
blink_detector = BlinkDetector()
dist_queue = deque(maxlen=5)
cam = cv2.VideoCapture(0)
print("📸 Bắt đầu điểm danh thông minh... (ESC để thoát)")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes, _ = mtcnn.detect(rgb)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if boxes is not None:
        for box in boxes:
            face = extract_face_region(rgb, box)
            if face is None:
                continue

            # Nhận diện real/fake
            label_rf, score_rf = analyze_image(face)

            # Nhận diện danh tính (ArcFace)
            emb = embedding_from_face(face)
            if emb is None:
                continue
            dists = np.linalg.norm(known_faces['encodings'] - emb, axis=1)
            min_d, idx = np.min(dists), np.argmin(dists)
            dist_queue.append(min_d)
            avg_d = np.mean(dist_queue)
            name = known_faces['names'][idx] if avg_d < THRESHOLD else "Unknown"

            # Blink detection
            blinks = blink_detector.update(gray, box)

            # Đánh giá kết hợp: nếu fake hoặc không chớp mắt => nghi ngờ
            status = "REAL ✅" if (label_rf == "REAL" and blinks > 0) else "FAKE ⚠️"
            color = (0, 255, 0) if status.startswith("REAL") else (0, 0, 255)

            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 2)
            cv2.putText(frame, f"{name} | {status}", (int(box[0]), int(box[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            print(f"[DEBUG] {name} | Dist={avg_d:.3f} | RF={label_rf}:{score_rf:.1f}% | Blinks={blinks}")

    cv2.imshow("Smart Face Attendance (ArcFace + Fake + Blink)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cam.release()
cv2.destroyAllWindows()
