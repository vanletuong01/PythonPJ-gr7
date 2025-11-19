import numpy as np
import pymysql
import os
import pickle  # Thêm import pickle
from backend.app.ai.face.fake_detector import FakeDetector

fake_detector_instance = FakeDetector()  # Thêm dòng này trước khi dùng

def load_all_embeddings():
    """
    Return:
    {
        "encodings": np.ndarray (N,512)
        "meta": list[{id, name, student_code, ...}]
    }
    """
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "python_project"),
        charset="utf8mb4"
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.StudentID, s.FullName, s.StudentCode, e.Embedding
        FROM student s
        JOIN student_embeddings e ON s.StudentID = e.StudentID
    """)
    rows = cursor.fetchall()
    print(f"DEBUG: Số dòng JOIN được: {len(rows)}")

    encs = []
    meta = []

    for rid, name, code, emb_blob in rows:
        try:
            print(f"DEBUG: Kích thước BLOB: {len(emb_blob)} bytes")
            emb = pickle.loads(emb_blob)  # Đọc embedding bằng pickle
            print(f"DEBUG: emb.shape = {emb.shape}")
            if emb.shape[0] == 512:
                encs.append(emb)
                meta.append({
                    "id": rid,
                    "name": name,
                    "code": code
                })
        except Exception as e:
            print(f"ERROR: {e}")
            continue

    conn.close()

    print(f"DEBUG: Số embedding hợp lệ: {len(encs)}")

    if len(encs) == 0:
        return {"encodings": np.zeros((0, 512), dtype="float32"), "meta": []}

    return {
        "encodings": np.vstack(encs),
        "meta": meta
    }