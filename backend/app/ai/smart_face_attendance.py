import cv2
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
from backend.app.ai.student_embedding import load_all_embeddings ,fake_detector_instance
from backend.app.ai.face.fake_detector import FakeDetector
from backend.app.ai.face.detector import detect_faces_rgb, extract_face_region_rgb
import pymysql
import os

embedder = ArcfaceEmbedder()
_known = load_all_embeddings()


def match_image_and_check_real(image_np_bgr):

    rgb = cv2.cvtColor(image_np_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)

    boxes, probs = detect_faces_rgb(pil)
    if boxes is None or len(boxes) == 0:
        return {'status': 'no_face'}

    idx = np.argmax([(b[2] - b[0]) * (b[3] - b[1]) for b in boxes])
    box = boxes[idx]

    face_rgb = extract_face_region_rgb(rgb, box)
    if face_rgb is None:
        return {'status': 'error'}

    face_bgr = face_rgb[:, :, ::-1]

    emb = embedder.get_embedding(face_bgr)
    if emb is None:
        return {'status': 'embed_fail'}

    global _known
    if _known["encodings"].size == 0:
        _known = load_all_embeddings()
        if _known["encodings"].size == 0:
            return {"status": "no_db"}

    sims = cosine_similarity([emb], _known["encodings"])[0]
    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])
    student = _known["meta"][best_idx]

    fake_result = fake_detector_instance.process_frame(image_np_bgr)
    real_conf_fake = fake_result["real_conf"]

    real_conf = 0.6 * best_score + 0.4 * real_conf_fake

    return {
        "status": "ok",
        "found": best_score >= 0.55,
        "similarity": best_score,
        "student": student,
        "is_real": real_conf >= 0.55,
        "real_conf": real_conf,
        "debug": {
            "emb_sim": best_score,
            "fake_real_conf": real_conf_fake
        }
    }


def save_attendance_to_db(study_id, photo_path):
    """
    Lưu thông tin điểm danh vào bảng attendance.
    """
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "python_project"),
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    sql = """
        INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
        VALUES (%s, CURDATE(), CURTIME(), %s)
    """
    cursor.execute(sql, (study_id, photo_path))
    conn.commit()
    conn.close()