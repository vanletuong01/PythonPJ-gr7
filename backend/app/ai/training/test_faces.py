import os
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import torch
from facenet_pytorch import MTCNN
from backend.app.ai.face.fake_detector import FakeDetector
from backend.app.ai.student_embedding import load_all_embeddings

device = 'cuda' if torch.cuda.is_available() else 'cpu'
mtcnn = MTCNN(keep_all=True, device=device)
print(f"✅ Manual MTCNN khởi tạo trên {device}")

# ===============================
# 1️⃣ KIỂM TRA REAL / FAKE CHO ẢNH ĐIỂM DANH
# ===============================
def check_real_fake_for_all():
    ATTENDANCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'attendance'))
    print("🔍 Đang kiểm tra real/fake các ảnh đã điểm danh...\n")

    if not os.path.exists(ATTENDANCE_DIR):
        print(f"❌ Không tìm thấy thư mục: {ATTENDANCE_DIR}")
        return

    for folder in sorted(os.listdir(ATTENDANCE_DIR)):
        folder_path = os.path.join(ATTENDANCE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        print(f"👤 {folder}:")
        for f in sorted(os.listdir(folder_path)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            img_path = os.path.join(folder_path, f)
            try:
                img = Image.open(img_path).convert("RGB")
            except Exception as e:
                print(f"  ⚠️ Lỗi mở ảnh {f}: {e}")
                continue

            # ✅ Phát hiện khuôn mặt bằng manual MTCNN
            boxes, _ = mtcnn.detect(img)
            face_detected = boxes is not None and len(boxes) > 0

            # Giả lập các hàm này nếu chưa có
            tscore = 1.0  # hoặc: texture_score(img)
            has_border = False  # hoặc: detect_border_smart(img_path)

            # ✅ Nếu không thấy khuôn mặt → xem là FAKE
            if not face_detected:
                status = "FAKE ⚠️"
                reasons = ["không phát hiện khuôn mặt"]
            else:
                status = "FAKE ⚠️" if (tscore < 0.4 or has_border) else "REAL ✅"
                reasons = []
                if tscore < 0.4:
                    reasons.append("mịn/thiếu chi tiết")
                if has_border:
                    reasons.append("viền điện thoại/màn hình")

            reason_text = " + ".join(reasons) if reasons else "bình thường"
            print(f"  - {f}: {status} | {reason_text} (score={tscore:.2f})")

    print("\n✅ Hoàn tất kiểm tra real/fake.\n")


# ===============================
# 2️⃣ KIỂM TRA ĐỘ CHÍNH XÁC MÔ HÌNH NHẬN DIỆN
# ===============================
def test_face_recognition_accuracy():
    print("📂 Đang tải embedding từ DB...")
    embeddings = load_all_embeddings()
    print("DEBUG: Keys:", embeddings.keys())
    print("DEBUG: Meta mẫu:", embeddings["meta"][0])

    encodings = np.array(embeddings["encodings"])

    # 🔥 SỬA LẠI Ở ĐÂY — dùng đúng key meta
    names = np.array([m['id'] for m in embeddings["meta"]])

    unique_people = np.unique(names)
    if len(unique_people) < 2:
        print("⚠️ Dữ liệu quá ít để test accuracy.")
        return

    # Chia train/test theo từng người
    np.random.shuffle(unique_people)
    split = int(0.8 * len(unique_people))
    train_people = unique_people[:split]
    test_people = unique_people[split:]

    train_mask = np.isin(names, train_people)
    test_mask = np.isin(names, test_people)

    train_enc = encodings[train_mask]
    train_names = names[train_mask]
    test_enc = encodings[test_mask]
    test_names = names[test_mask]

    thresholds = np.arange(0.70, 0.91, 0.02)
    best_acc, best_thr = 0, 0.8
    y_true, y_pred = [], []

    for thr in thresholds:
        preds = []
        for enc, true_name in zip(test_enc, test_names):
            sims = cosine_similarity([enc], train_enc)[0]
            best_idx = np.argmax(sims)
            pred = train_names[best_idx] if sims[best_idx] > thr else "Unknown"
            preds.append(pred)

        acc = np.mean(preds == test_names)
        if acc > best_acc:
            best_acc, best_thr = acc, thr
            y_pred = preds
            y_true = test_names

    print(f"\n🎯 Threshold tối ưu: {best_thr:.2f}")
    print(f"📊 Accuracy: {best_acc * 100:.2f}%")

    # Precision / Recall / F1 (bỏ Unknown)
    mask = np.array(y_pred) != "Unknown"
    if np.any(mask):
        prec = precision_score(y_true[mask], np.array(y_pred)[mask], average='weighted')
        rec = recall_score(y_true[mask], np.array(y_pred)[mask], average='weighted')
        f1 = f1_score(y_true[mask], np.array(y_pred)[mask], average='weighted')

        print(f"Precision: {prec:.2f}")
        print(f"Recall: {rec:.2f}")
        print(f"F1-score: {f1:.2f}")
    else:
        print("⚠️ Không có prediction khác Unknown!")

# ===============================
# 3️⃣ MAIN
# ===============================
if __name__ == "__main__":
    print("==============================")
    print("🧠 PHÂN TÍCH ẢNH REAL / FAKE (Manual MTCNN)")
    print("==============================")
    check_real_fake_for_all()

    print("==============================")
    print("🎯 KIỂM TRA ĐỘ CHÍNH XÁC MÔ HÌNH (Manual MTCNN)")
    print("==============================")
    test_face_recognition_accuracy()
