import json
import numpy as np
from backend.app.db.database import get_connection

# Lưu embedding (512 floats) vào DB
def save_embedding(student_id: int, embedding):
    try:
        conn = get_connection()
        cur = conn.cursor()

        emb_json = json.dumps(embedding.tolist())

        # Nếu đã có thì update
        cur.execute("""
            SELECT ID FROM student_embedding WHERE StudentID = %s
        """, (student_id,))
        row = cur.fetchone()

        if row:
            cur.execute("""
                UPDATE student_embedding
                SET Embedding = %s
                WHERE StudentID = %s
            """, (emb_json, student_id))
        else:
            cur.execute("""
                INSERT INTO student_embedding (StudentID, Embedding)
                VALUES (%s, %s)
            """, (student_id, emb_json))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("save_embedding error:", e)
        return False



# Lấy tất cả embedding để so khớp
def load_all_embeddings():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT e.StudentID, u.StudentName, e.Embedding
            FROM student_embedding e
            LEFT JOIN students u ON u.StudentID = e.StudentID
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        encodings = []
        meta = []

        for row in rows:
            student_id = row[0]
            student_name = row[1]
            emb_json = row[2]

            emb = json.loads(emb_json)
            encodings.append(emb)
            meta.append({
                "student_id": student_id,
                "student_name": student_name
            })

        return {
            "encodings": np.array(encodings),
            "meta": meta
        }

    except Exception as e:
        print("load_all_embeddings error:", e)
        return {
            "encodings": np.array([]),
            "meta": []
        }
