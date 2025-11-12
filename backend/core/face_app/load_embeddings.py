import numpy as np
from deepface import DeepFace
from backend.db.database import get_connection

def load_embeddings_from_mysql(limit=None):
    """
    Tải tất cả embedding khuôn mặt từ MySQL.
    Trả về:
        known_faces: np.ndarray có shape (N, 512)
        known_names: list tên hoặc mã sinh viên
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT StudentID, Embedding FROM student_embeddings"
        if limit:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            print("[⚠️] Không có bản ghi embedding nào trong bảng student_embeddings.")
            return np.empty((0, 512), dtype=np.float32), []

        known_faces = []
        known_names = []

        for i, row in enumerate(rows):
            student_id = row.get("StudentID")
            emb_data = row.get("Embedding")

            # Kiểm tra dữ liệu hợp lệ
            if not emb_data:
                print(f"[⚠️] Bỏ qua hàng {i}: Embedding trống cho StudentID = {student_id}")
                continue

            try:
                emb = np.frombuffer(emb_data, dtype=np.float32)

                if emb.size != 512:
                    print(f"[⚠️] Bỏ qua hàng {i}: Kích thước embedding {emb.size} ≠ 512 (StudentID={student_id})")
                    continue

                known_faces.append(emb)
                known_names.append(student_id)

            except Exception as e:
                print(f"[❌] Lỗi khi giải mã embedding hàng {i} (StudentID={student_id}): {e}")

        cursor.close()
        conn.close()

        known_faces = np.array(known_faces, dtype=np.float32)
        print(f"[✅] Đã tải {len(known_faces)} embedding hợp lệ từ MySQL.")

        return known_faces, known_names

    except Exception as e:
        print(f"[❌] Lỗi khi tải embedding từ MySQL: {e}")
        return np.empty((0, 512), dtype=np.float32), []


# ==========================================================
# 🧠 HÀM SINH EMBEDDING CHO 1 ẢNH (DÙNG LÚC ĐĂNG KÝ & ĐIỂM DANH)
# ==========================================================
def extract_face_embedding(image_path):
    """
    Sinh embedding khuôn mặt (512 chiều) từ ảnh đầu vào.
    Dùng model ArcFace để đảm bảo thống nhất pipeline nhận diện.
    """
    try:
        result = DeepFace.represent(
            img_path=image_path,
            model_name="ArcFace",
            enforce_detection=False
        )

        if isinstance(result, list) and len(result) > 0:
            emb = np.array(result[0]["embedding"], dtype=np.float32)
            if emb.size == 512:
                return emb
            else:
                print(f"[⚠️] Embedding có kích thước khác 512 ({emb.size}), bỏ qua.")
                return None
        else:
            print("[⚠️] DeepFace không trả về embedding hợp lệ.")
            return None

    except Exception as e:
        print(f"[❌] Lỗi khi tạo embedding từ ảnh: {e}")
        return None
