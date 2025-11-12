import os
import pickle
import numpy as np
import cv2
from deepface import DeepFace
from tqdm import tqdm
import hashlib
from datetime import datetime
import random
from PIL import Image
import torch
from facenet_pytorch import MTCNN

# ===============================
# ⚙️ CẤU HÌNH
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "data", "face")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FACE_VARIANCE_THRESHOLD = 120  # Ngưỡng phát hiện ảnh mờ

print("🚀 Đang khởi tạo ArcFace + MTCNN (thủ công)...")

MODEL_NAME = "ArcFace"

# ✅ Khởi tạo model ArcFace một lần để cache
model = DeepFace.build_model(MODEL_NAME)

# ✅ Khởi tạo MTCNN thủ công
device = 'cuda' if torch.cuda.is_available() else 'cpu'
mtcnn = MTCNN(keep_all=True, device=device)
print(f"✅ MTCNN thủ công khởi tạo trên {device}")


# ===============================
# 🧩 HÀM HỖ TRỢ
# ===============================
def hash_image(img_path):
    """Sinh hash duy nhất cho ảnh"""
    with open(img_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_blurry(img):
    """Kiểm tra ảnh có bị mờ không"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() < FACE_VARIANCE_THRESHOLD

def extract_face_embedding(image_path):
    """Phát hiện + trích xuất embedding khuôn mặt (ArcFace + MTCNN thủ công)"""
    try:
        img = cv2.imread(image_path)
        if img is None or is_blurry(img):
            return None

        # Chuyển sang RGB cho MTCNN
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # ✅ Phát hiện khuôn mặt
        boxes, _ = mtcnn.detect(img_rgb)
        if boxes is None or len(boxes) == 0:
            return None

        # Cắt khuôn mặt đầu tiên
        x1, y1, x2, y2 = [int(v) for v in boxes[0]]
        face = img_rgb[y1:y2, x1:x2]

        # Nếu không cắt được mặt
        if face.size == 0:
            return None

        # ✅ Chuyển đúng dtype và định dạng
        face = np.array(face, dtype=np.uint8)

        # ✅ Trích xuất embedding trực tiếp bằng mảng numpy (không dùng img_path)
        result = DeepFace.represent(
            img_path=face,
            model_name=MODEL_NAME,
            enforce_detection=False
        )

        if result and len(result) > 0:
            embedding = np.array(result[0]["embedding"], dtype=np.float32)
            norm = np.linalg.norm(embedding)
            if norm == 0:
                return None
            embedding /= norm  # chuẩn hóa vector
            return embedding

        return None

    except Exception as e:
        print(f"❌ Không trích xuất được embedding: {e}")
        return None


# ===============================
# 🔀 CHIA TRAIN / TEST
# ===============================
def split_people(dataset_path, test_ratio=0.2):
    people = [p for p in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, p))]
    random.shuffle(people)
    n_test = max(1, int(len(people) * test_ratio))
    return set(people[n_test:]), set(people[:n_test])


# ===============================
# 🧠 TẠO EMBEDDING
# ===============================
def generate_embeddings(people_list):
    encodings, names, hashes = [], [], []
    total_faces, skipped = 0, 0

    for person_name in sorted(people_list):
        person_folder = os.path.join(DATASET_PATH, person_name)
        if not os.path.isdir(person_folder):
            continue

        print(f"\n🧍 Người: {person_name}")
        for image_name in tqdm(sorted(os.listdir(person_folder))):
            if not image_name.lower().endswith((".jpg", ".png", ".jpeg")):
                continue

            image_path = os.path.join(person_folder, image_name)
            emb = extract_face_embedding(image_path)
            if emb is None:
                skipped += 1
                continue

            encodings.append(emb)
            names.append(person_name)
            hashes.append(hash_image(image_path))
            total_faces += 1

    return encodings, names, hashes, total_faces, skipped


# ===============================
# 🎯 CHẠY CHÍNH
# ===============================
def main():
    print("\n🔹 TẠO EMBEDDING KHUÔN MẶT (ArcFace + MTCNN thủ công)\n")

    train_people, test_people = split_people(DATASET_PATH, test_ratio=0.2)
    print(f"🧩 Train: {len(train_people)} người | Test: {len(test_people)} người")

    for mode, people in [("train", train_people), ("test", test_people)]:
        print(f"\n===== 🔰 XỬ LÝ {mode.upper()} =====")
        encodings, names, hashes, total_faces, skipped = generate_embeddings(people)

        output_path = os.path.join(OUTPUT_DIR, f"face_encodings_{mode}_deep_arcface.pkl")
        with open(output_path, "wb") as f:
            pickle.dump({
                "encodings": encodings,
                "names": names,
                "hashes": hashes,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "num_people": len(set(names)),
                "num_embeddings": len(encodings),
                "avg_len_embedding": int(np.mean([len(e) for e in encodings]) if encodings else 0),
                "model": "DeepFace-ArcFace",
                "detector": "Manual-MTCNN"
            }, f)

        print(f"\n✅ Đã lưu: {output_path}")
        print(f"📊 Ảnh hợp lệ: {total_faces} | Bỏ qua: {skipped}")
        print(f"👥 Số người: {len(set(names))}\n")

    print("\n🎯 Hoàn tất! Embedding Deep-ArcFace (Manual MTCNN) đã được sinh.\n")


if __name__ == "__main__":
    main()
