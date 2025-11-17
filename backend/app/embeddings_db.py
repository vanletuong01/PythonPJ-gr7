import mysql.connector
import numpy as np
from backend.app.database import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True  # ← thêm để tránh lỗi unread result
    )

# ==========================================================
# 1️⃣ Thêm hoặc cập nhật embedding sinh viên
# ==========================================================
def insert_embedding(student_code, embedding, photo_path=None, quality=None, source="capture", full_name=None):
    conn = get_connection()
    cursor = conn.cursor(buffered=True)  # ← buffered=True
    try:
        # --- Kiểm tra dữ liệu hợp lệ ---
        if embedding is None or not isinstance(embedding, np.ndarray):
            print("❌ Lỗi: embedding không hợp lệ (None hoặc không phải numpy array).")
            return

        # --- Chuẩn hóa embedding (rất quan trọng) ---
        embedding = embedding.astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm == 0 or np.isnan(norm):
            print("❌ Lỗi: embedding bị lỗi (norm=0 hoặc NaN).")
            return
        embedding /= norm

        # --- Chuyển sang bytes để lưu vào DB ---
        embedding_bytes = embedding.tobytes()
        embedding_dim = len(embedding)

        # --- Kiểm tra sinh viên đã có chưa ---
        cursor.execute("SELECT StudentID FROM student WHERE StudentCode=%s", (student_code,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                INSERT INTO student (FullName, StudentCode, MajorID, TypeID)
                VALUES (%s, %s, %s, %s)
            """, (full_name or "Unknown", student_code, 1, 1))
            conn.commit()
            cursor.execute("SELECT LAST_INSERT_ID() AS id")
            student_id = cursor.fetchone()["id"]
            print(f"🆕 Thêm sinh viên mới: {student_code} (StudentID={student_id})")
        else:
            student_id = row["StudentID"]

        # --- Kiểm tra xem đã có embedding chưa ---
        cursor.execute("SELECT EmbeddingID FROM student_embeddings WHERE StudentID = %s", (student_id,))
        emb_exist = cursor.fetchone()

        if emb_exist:
            cursor.execute("""
                UPDATE student_embeddings
                SET Embedding = %s, EmbeddingDim = %s, PhotoPath = %s, Quality = %s, Source = %s, CreatedAt = NOW()
                WHERE StudentID = %s
            """, (embedding_bytes, embedding_dim, photo_path, quality, source, student_id))
            print(f"🔄 Cập nhật embedding cho StudentID = {student_id}")
        else:
            cursor.execute("""
                INSERT INTO student_embeddings (StudentID, Embedding, EmbeddingDim, PhotoPath, Quality, Source)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (student_id, embedding_bytes, embedding_dim, photo_path, quality, source))
            print(f"✅ Đã lưu embedding mới cho StudentID = {student_id}")

        conn.commit()

    except mysql.connector.Error as e:
        print("❌ Lỗi khi lưu embedding:", e)

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 2️⃣ Tải toàn bộ embedding để nhận diện
# ==========================================================
def load_all_embeddings():
    """Lấy toàn bộ embedding + thông tin sinh viên từ MySQL."""
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    try:
        cursor.execute("SELECT e.StudentID, e.Embedding, s.StudentCode FROM student_embeddings e JOIN student s ON e.StudentID=s.StudentID")
        rows = cursor.fetchall()
        return [(r[0], np.frombuffer(r[1], dtype=np.float32), r[2]) for r in rows]
    finally:
        cursor.close()
        conn.close()
