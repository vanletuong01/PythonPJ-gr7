import os
import cv2
import numpy as np

RAW_DIR = os.path.join("data", "face")
OUTPUT_DIR = os.path.join("data", "face_preprocessed")
TARGET_SIZE = (112, 112)  # ✅ Chuẩn ArcFace

os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_image(img):
    """Kiểm tra ảnh có hợp lệ không (không đen, không nhỏ)"""
    if img is None or img.size == 0:
        return False
    if np.mean(img) < 5:  # quá tối
        return False
    h, w = img.shape[:2]
    return h > 50 and w > 50

for person in os.listdir(RAW_DIR):
    person_dir = os.path.join(RAW_DIR, person)
    if not os.path.isdir(person_dir):
        continue

    save_dir = os.path.join(OUTPUT_DIR, person)
    os.makedirs(save_dir, exist_ok=True)

    for img_name in os.listdir(person_dir):
        img_path = os.path.join(person_dir, img_name)
        img = cv2.imread(img_path)

        if not is_valid_image(img):
            print(f"⚠️ Ảnh lỗi hoặc quá nhỏ: {img_path}")
            continue

        # Chuyển sang RGB và resize chuẩn ArcFace
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, TARGET_SIZE)

        # Lưu lại
        new_name = os.path.splitext(img_name)[0] + ".jpg"
        save_path = os.path.join(save_dir, new_name)
        cv2.imwrite(save_path, cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR))

print("✅ Đã chuẩn hóa toàn bộ ảnh khuôn mặt cho ArcFace và FakeDetector!")
