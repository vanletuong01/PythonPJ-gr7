# ===============================================
# backend/db/repositories/embeddings_repo.py
# ===============================================

import mysql.connector
import numpy as np
from backend.db.database import get_connection


class EmbeddingRepository:
    """Repository quản lý CRUD cho bảng student_embeddings"""

    # ==========================================================
    # 1️⃣ Thêm hoặc cập nhật embedding sinh viên
    # ==========================================================
    def insert_or_update_embedding(self, student_code, embedding, photo_path=None, quality=None, source="capture", full_name=None):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # --- Kiểm tra dữ liệu hợp lệ ---
            if embedding is None or not isinstance(embedding, np.ndarray):
                print("❌ Lỗi: embedding không hợp lệ (None hoặc không phải numpy array).")
                return False

            # --- Chuẩn hóa embedding ---
            embedding = embedding.astype(np.float32)
            norm = np.linalg.norm(embedding)
            if norm == 0 or np.isnan(norm):
                print("❌ Lỗi: embedding bị lỗi (norm=0 hoặc NaN).")
                return False
            embedding /= norm

            # --- Chuyển sang bytes ---
            embedding_bytes = embedding.tobytes()
            embedding_dim = len(embedding)

            # --- Kiểm tra sinh viên ---
            cursor.execute("SELECT StudentID FROM student WHERE StudentCode = %s", (student_code,))
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
            return True

        except mysql.connector.Error as e:
            print("❌ Lỗi khi lưu embedding:", e)
            return False

        finally:
            cursor.close()
            conn.close()

    # ==========================================================
    # 2️⃣ Lấy toàn bộ embedding để nhận diện
    # ==========================================================
    def get_all_embeddings(self):
        """Trả về embeddings (numpy array) + metadata sinh viên và StudyID"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT se.StudentID, se.Embedding, s.FullName, s.StudentCode, st.StudyID
                FROM student_embeddings se
                JOIN student s ON s.StudentID = se.StudentID
                LEFT JOIN study st ON s.StudentID = st.StudentID
            """)
            rows = cursor.fetchall()

            embeddings = []
            meta = []

            for row in rows:
                emb = np.frombuffer(row["Embedding"], dtype=np.float32)

                norm = np.linalg.norm(emb)
                if norm == 0 or np.isnan(norm):
                    print(f"⚠️ Embedding lỗi (StudentID={row['StudentID']}) — bỏ qua.")
                    continue
                emb /= norm

                embeddings.append(emb)
                meta.append({
                    "StudentID": row["StudentID"],
                    "FullName": row["FullName"],
                    "StudentCode": row["StudentCode"],
                    "StudyID": row["StudyID"]
                })

            if len(embeddings) == 0:
                print("⚠️ Chưa có embedding nào trong DB.")
                return np.array([], dtype=np.float32), []

            print(f"✅ Đã load {len(embeddings)} embeddings từ MySQL.")
            return np.vstack(embeddings), meta

        finally:
            cursor.close()
            conn.close()
