# =========================================
# 📂 backend/register_capture.py
# Mục đích: Xử lý camera, chụp ảnh khuôn mặt và lưu ảnh thô.
# Không tương tác DB hoặc sinh embedding.
# =========================================

import os
import cv2
import unicodedata
from datetime import datetime

# =========================================
# 1️⃣ Cấu hình
# =========================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "uploads", "faces_tmp")
os.makedirs(TEMP_DIR, exist_ok=True)

# =========================================
# 2️⃣ Tiện ích
# =========================================
def remove_vietnamese_tones(text: str):
    """Loại bỏ dấu tiếng Việt để đặt tên folder/file an toàn."""
    import unicodedata
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# =========================================
# 3️⃣ Hàm chụp ảnh
# =========================================
def register_student_capture(student_code: str, full_name: str, capture_count: int = 25):
    """
    Mở webcam, hướng dẫn người dùng chụp ảnh khuôn mặt.
    Lưu ảnh vào thư mục tạm ./uploads/faces_tmp/{student_code}/
    """
    # Tạo thư mục lưu tạm
    safe_name = remove_vietnamese_tones(full_name).replace(" ", "")
    folder_name = f"{student_code}_{safe_name}"
    save_dir = os.path.join(TEMP_DIR, folder_name)
    os.makedirs(save_dir, exist_ok=True)

    # Mở webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Không thể mở camera.")
        return None

    print(f"📸 Bắt đầu chụp ảnh cho {full_name} ({student_code})")
    print("➡ Nhấn phím 'C' để chụp, 'Q' để thoát.")

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Không thể đọc khung hình từ camera.")
            break

        # Hiển thị khung hình
        cv2.imshow("Capture Face", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            count += 1
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{count}.jpg"
            save_path = os.path.join(save_dir, filename)
            cv2.imwrite(save_path, frame)
            print(f"✅ Ảnh {count} đã lưu: {save_path}")

            if count >= capture_count:
                print("🎯 Đã chụp đủ số lượng ảnh yêu cầu.")
                break

        elif key == ord('q'):
            print("🛑 Dừng chụp theo yêu cầu người dùng.")
            break

    cap.release()
    cv2.destroyAllWindows()

    if count == 0:
        print("⚠️ Không có ảnh nào được chụp.")
        return None

    print(f"📦 Đã lưu {count} ảnh tại: {save_dir}")
    return save_dir


# =========================================
# 4️⃣ Chạy độc lập (test nhanh)
# =========================================
if __name__ == "__main__":
    register_student_capture("SV001", "Nguyễn Văn A")
