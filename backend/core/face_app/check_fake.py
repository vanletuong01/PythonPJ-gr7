import cv2
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
from datetime import datetime
from utils.fake_detector import texture_score

# ===============================
# 1️⃣ CẤU HÌNH MÔI TRƯỜNG
# ===============================
device = 'cuda' if torch.cuda.is_available() else 'cpu'
mtcnn = MTCNN(keep_all=True, device=device)
arcface_model = InceptionResnetV1(pretrained='vggface2').eval().to(device)

print(f"🧠 Device: {device}")

# ===============================
# 2️⃣ KẾT NỐI CƠ SỞ DỮ LIỆU
# ===============================
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="face_attendance"
    )

# ===============================
# 3️⃣ PHÁT HIỆN VIỀN MÀN HÌNH (FAKE)
# ===============================
def detect_border_or_screen(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 150)
    h, w = gray.shape
    border_ratio = (
        np.mean(edges[:int(0.05*h), :]) +
        np.mean(edges[-int(0.05*h):, :]) +
        np.mean(edges[:, :int(0.05*w)]) +
        np.mean(edges[:, -int(0.05*w):])
    ) / 4
    contrast = gray.std()
    return border_ratio > 20 or contrast < 30

# ===============================
# 4️⃣ TRÍCH XUẤT VECTOR ARC_FACE
# ===============================
def extract_arcface_embedding(frame):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face_tensor = mtcnn(img)
    if face_tensor is None:
        return None
    with torch.no_grad():
        embeddings = arcface_model(face_tensor.to(device)).cpu().numpy()
    return embeddings[0] if len(embeddings) > 0 else None

# ===============================
# 5️⃣ GHI ĐIỂM DANH VÀO DB
# ===============================
def mark_attendance(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT StudyID FROM study WHERE StudentID = %s LIMIT 1", (student_id,))
    result = cur.fetchone()

    if not result:
        print("⚠️ Không tìm thấy StudyID cho StudentID:", student_id)
        return

    study_id = result[0]
    now = datetime.now()
    photo_path = f"photos/{student_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"

    cur.execute("""
        INSERT INTO attendance (StudyID, StudentID, Date, Time, PhotoPath)
        VALUES (%s, %s, CURDATE(), CURTIME(), %s)
    """, (study_id, student_id, photo_path))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Đã ghi điểm danh cho StudentID={student_id}")

# ===============================
# 6️⃣ NHẬN DIỆN VÀ GHI DANH
# ===============================
def check_real_fake_from_camera(known_faces, known_ids):
    cap = cv2.VideoCapture(0)
    print("🎥 Camera đang mở... Nhấn 'q' để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Không thể truy cập camera.")
            break

        label = "Đang kiểm tra..."
        color = (255, 255, 255)

        if detect_border_or_screen(frame):
            label = "❌ FAKE (BORDER)"
            color = (0, 0, 255)
        else:
            img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tscore = texture_score(img_pil)

            if tscore < 0.5:
                label = f"❌ FAKE ({tscore:.2f})"
                color = (0, 0, 255)
            else:
                emb = extract_arcface_embedding(frame)
                if emb is not None:
                    sims = cosine_similarity([emb], known_faces)[0]
                    best_idx = np.argmax(sims)
                    best_score = sims[best_idx]
                    best_id = known_ids[best_idx]

                    if best_score > 0.85:
                        label = f"✅ ID={best_id} ({best_score:.3f})"
                        color = (0, 255, 0)
                        mark_attendance(best_id)
                    else:
                        label = f"❌ Không trùng (max={best_score:.2f})"
                        color = (0, 0, 255)
                else:
                    label = "⚠️ Không thấy mặt"
                    color = (255, 255, 0)

        cv2.putText(frame, label, (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.imshow("Face Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ===============================
# 7️⃣ CHẠY CHÍNH
# ===============================
if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_id, embedding FROM students WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    known_faces = []
    known_ids = []
    for sid, emb_blob in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        known_faces.append(emb)
        known_ids.append(sid)

    known_faces = np.array(known_faces)
    print(f"✅ Đã tải {len(known_ids)} embedding hợp lệ từ MySQL.")
    check_real_fake_from_camera(known_faces, known_ids)
