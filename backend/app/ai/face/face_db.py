# face_db.py
# Helper load embeddings từ pickle (models/face_encodings.pkl)
# Có thêm helper optional để load từ MySQL nếu bạn muốn ghi/đọc từ DB

import os
import pickle
import numpy as np

PICKLE_PATH = os.path.join("models","face_encodings.pkl")

def load_encodings(pickle_path=PICKLE_PATH):
    if not os.path.exists(pickle_path):
        return {"encodings": np.array([], dtype=np.float32), "names": [], "meta": []}
    with open(pickle_path, "rb") as f:
        obj = pickle.load(f)
    # đảm bảo dtype numpy
    enc = obj.get("encodings")
    if isinstance(enc, list):
        enc = np.vstack(enc).astype(np.float32)
    obj["encodings"] = enc
    return obj

# Optional: load embeddings from MySQL if you store binary embeddings there
def load_from_mysql(get_connection_fn):
    """
    get_connection_fn: callable trả connection (mysql.connector)
    Trả về obj như load_encodings
    """
    import numpy as np
    conn = get_connection_fn()
    cur = conn.cursor()
    cur.execute("SELECT StudentID, Embedding FROM student_embeddings WHERE Embedding IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    encs = []
    names = []
    for r in rows:
        sid, emb_blob = r
        try:
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            if emb.size == 512:
                encs.append(emb)
                names.append(str(sid))
        except Exception:
            continue
    if len(encs) == 0:
        return {"encodings": np.array([], dtype=np.float32), "names": [], "meta": []}
    return {"encodings": np.vstack(encs).astype(np.float32), "names": names, "meta": []}

if __name__ == "__main__":
    o = load_encodings()
    print("Loaded", len(o.get("names",[])))
