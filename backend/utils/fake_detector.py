# face_app/fake_detector_v3.py
import os
import cv2
import csv
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from skimage import feature
from facenet_pytorch import MTCNN
import warnings
warnings.filterwarnings("ignore")

# DeepFace cho ArcFace backend
try:
    from deepface import DeepFace
except Exception as e:
    DeepFace = None
    print("⚠️ Warning: DeepFace không được import:", e)

# ===============================
# 1️⃣ CẤU HÌNH ĐƯỜNG DẪN & THIẾT BỊ
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
ATTENDANCE_DIR = os.path.join(DATA_DIR, 'attendance')
REPORT_PATH = os.path.join(BASE_DIR, '..', 'report_face_real_fake_v3.csv')
MODEL_WEIGHTS = os.path.join(BASE_DIR, 'fake_detector_v3_arcface.pth')

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🧠 Device: {device}")

# ===============================
# 2️⃣ KHỞI TẠO MTCNN + DeepFace ArcFace (model load 1 lần)
# ===============================
mtcnn = MTCNN(image_size=112, margin=10, post_process=True, keep_all=False, device=device)

deepface_model = None
if DeepFace is not None:
    try:
        # Build/load ArcFace model (DeepFace). Đây là model Keras/TF trong DeepFace.
        deepface_model = DeepFace.build_model("ArcFace")
        print("✅ DeepFace ArcFace model ready.")
    except Exception as e:
        deepface_model = None
        print("⚠️ Không thể build DeepFace ArcFace model:", e)
else:
    print("⚠️ DeepFace chưa cài. Cài bằng: pip install deepface")

# ===============================
# 3️⃣ CÁC ĐẶC TRƯNG BỔ TRỢ
# ===============================
def texture_score(img: Image.Image) -> float:
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    lbp = feature.local_binary_pattern(gray, 8, 1, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 10), range=(0, 9))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)
    entropy = -np.sum(hist * np.log2(hist + 1e-6))
    return float(np.clip(entropy / 3.5, 0, 1))

def fft_feature(img: Image.Image) -> float:
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)
    h, w = magnitude.shape
    k = max(4, int(min(h, w) * 0.08))
    high_energy = np.mean(magnitude[-k:, -k:])
    return float(np.clip(high_energy / (magnitude.max() + 1e-6), 0, 1))

def moire_score(img: Image.Image) -> float:
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    mag = np.abs(fshift)
    high_freq_energy = np.sum(mag[mag > np.percentile(mag, 99.5)])
    total_energy = np.sum(mag) + 1e-6
    return float(np.clip(high_freq_energy / total_energy, 0, 1))

def detect_rectangular_frame(pil_img: Image.Image) -> float:
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 70, 150)
    h, w = edges.shape
    border_density = (
        np.sum(edges[:15, :]) + np.sum(edges[-15:, :]) +
        np.sum(edges[:, :15]) + np.sum(edges[:, -15:])
    ) / (h * w)
    return float(np.clip(border_density * 3, 0.0, 1.0))

# ===============================
# 4️⃣ MLP PHÂN LOẠI REAL/FAKE (512 + 4)
# ===============================
class ArcFaceFakeDetector(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(512 + 4, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, emb, extra):
        fused = torch.cat([emb, extra], dim=1)
        return self.fc(fused)

model = ArcFaceFakeDetector().to(device)
if os.path.exists(MODEL_WEIGHTS):
    try:
        model.load_state_dict(torch.load(MODEL_WEIGHTS, map_location=device))
        print("✅ Loaded trained weights:", MODEL_WEIGHTS)
    except Exception as e:
        print("⚠️ Lỗi load weights:", e)
else:
    print("⚠️ No trained weights found — using random MLP weights.")
model.eval()

FRAME_HARD_THRESHOLD = 0.35
FRAME_SOFT_THRESHOLD = 0.15

# ===============================
# 5️⃣ HÀM TRÍCH EMBEDDING BẰNG DEEPFACE (ArcFace)
# ===============================
def get_deepface_embedding(face_bgr):
    """
    face_bgr: numpy BGR crop của khuôn mặt (OpenCV)
    Trả về embedding chuẩn hóa (1D numpy float32) hoặc None
    """
    if deepface_model is None:
        raise RuntimeError("DeepFace model chưa được tải (DeepFace.build_model('ArcFace') thất bại).")

    # DeepFace.represent chấp nhận path hoặc np array (RGB). Chuyển sang RGB
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    try:
        rep = DeepFace.represent(
            img_path = face_rgb,
            model = deepface_model,
            model_name = "ArcFace",
            detector_backend = "skip",   # đã cắt sẵn
            enforce_detection = False
        )
        # represent trả về list of dicts; lấy embedding đầu tiên
        if isinstance(rep, list) and len(rep) > 0 and "embedding" in rep[0]:
            emb = np.array(rep[0]["embedding"], dtype=np.float32)
            emb = emb / (np.linalg.norm(emb) + 1e-6)
            return emb
        else:
            return None
    except Exception as e:
        print("⚠️ DeepFace.represent error:", e)
        return None

# ===============================
# 6️⃣ PHÂN TÍCH 1 ẢNH (MTCNN -> DeepFace ArcFace -> MLP)
# ===============================
def analyze_image(image_input, debug=False):
    """
    Trả về (label, score) cho 1 ảnh đường dẫn hoặc numpy image.
    """
    try:
        pil = Image.open(image_input).convert("RGB") if isinstance(image_input, str) \
              else Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        img_cv = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        # Dò mặt bằng MTCNN (trả bbox)
        boxes, probs = mtcnn.detect(pil)
        if boxes is None or len(boxes) == 0:
            return "NO_FACE", 0.0

        # dùng bbox đầu tiên
        x1, y1, x2, y2 = map(int, boxes[0])
        # clamp
        h, w = img_cv.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 - x1 <= 10 or y2 - y1 <= 10:
            return "NO_FACE", 0.0

        face_crop = img_cv[y1:y2, x1:x2].copy()

        # Tính các features phụ
        t = texture_score(pil)
        f = fft_feature(pil)
        m = moire_score(pil)
        frame_score = detect_rectangular_frame(pil)

        if frame_score > FRAME_HARD_THRESHOLD:
            return "FAKE", round((1.0 - frame_score) * 100, 2)

        # Trích embedding bằng DeepFace ArcFace
        emb = get_deepface_embedding(face_crop)
        if emb is None:
            return "NO_FACE", 0.0

        emb_tensor = torch.tensor([emb], dtype=torch.float32).to(device)
        extra_tensor = torch.tensor([[t, f, m, frame_score]], dtype=torch.float32).to(device)

        with torch.no_grad():
            pred = model(emb_tensor, extra_tensor).item()

        if frame_score > FRAME_SOFT_THRESHOLD:
            pred *= (1.0 - 0.7 * frame_score)

        label = "REAL" if pred > 0.5 else "FAKE"
        score = round(pred * 100, 2)

        if debug:
            print(f"[DEBUG] t={t:.2f}, f={f:.2f}, m={m:.2f}, frame={frame_score:.2f}, pred={pred:.3f} -> {label}")

        return label, score
    except Exception as e:
        print("⚠️ analyze_image error:", e)
        return "ERROR", 0.0

# ===============================
# 7️⃣ Phân tích toàn bộ thư mục
# ===============================
def analyze_all_images(data_dir=ATTENDANCE_DIR, output_csv=REPORT_PATH):
    results = []
    print("🔍 Đang phân tích REAL / FAKE bằng DeepFace(ArcFace) + MTCNN...\n")

    for person_name in sorted(os.listdir(data_dir)):
        person_folder = os.path.join(data_dir, person_name)
        if not os.path.isdir(person_folder):
            continue
        for image_name in sorted(os.listdir(person_folder)):
            image_path = os.path.join(person_folder, image_name)
            label, score = analyze_image(image_path)
            results.append({
                "person": person_name,
                "image": image_name,
                "score": score,
                "label": label
            })
            print(f"{person_name}/{image_name}: {label} ({score:.2f}%)")

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["person", "image", "score", "label"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Kết quả lưu tại: {output_csv}")

# ===============================
# 8️⃣ MAIN
# ===============================
if __name__ == "__main__":
    analyze_all_images()
