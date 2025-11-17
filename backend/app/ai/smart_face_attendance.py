import cv2
import numpy as np
from PIL import Image

from .detector import detect_faces_rgb
from .preprocess_faces import extract_face_region_rgb
from .arcface_embedder import get_embedding
from .face_db import load_all_embeddings
from .fake_detector import is_fake_by_rules

from sklearn.metrics.pairwise import cosine_similarity
from backend.app.db.database import get_connection

THRESHOLD_COSINE = 0.55
THRESHOLD_REAL_CONF = 0.55


# Load embeddings vào RAM khi khởi động
_known = load_all_embeddings()


def match_image_and_check_real(image_np_bgr):
    rgb = cv2.cvtColor(image_np_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)

    # 1. Detect face
    boxes, probs = detect_faces_rgb(pil)
    if boxes is None or len(boxes) == 0:
        return {'status': 'no_face'}

    # 2. Lấy khuôn mặt lớn nhất
    areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
    idx = int(np.argmax(areas))
    box = boxes[idx]

    face = extract_face_region_rgb(rgb, box)
    if face is None:
        return {'status': 'error', 'message': 'crop failed'}

    # 3. Embedding
    emb = get_embedding(face)
    if emb is None:
        return {'status': 'error', 'message': 'embed fail'}

    if _known['encodings'].size == 0:
        return {'status': 'no_db'}

    # 4. So khớp cosine
    sims = cosine_similarity([emb], _known['encodings'])[0]
    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])
    student = _known['meta'][best_idx] if best_idx < len(_known['meta']) else {}

    # 5. Kiểm tra giả mạo
    label_fake, fake_score = is_fake_by_rules(face)

    # fake_score (0..100) → scale 0..1
    fake_norm = fake_score / 100.0

    # REAL CONF = 40% fake detector + 60% face similarity
    real_conf = (fake_norm * 0.4) + (best_score * 0.6)

    is_real = real_conf >= THRESHOLD_REAL_CONF

    return {
        'status': 'ok',
        'found': best_score >= THRESHOLD_COSINE,
        'similarity': best_score,
        'student': student,
        'is_real': bool(is_real),
        'real_conf': float(real_conf),
        'fake_score': fake_score,
        'label_fake': label_fake
    }


def save_attendance_to_db(student_id, study_id, similarity, real_conf):
    try:
        if not student_id or not study_id:
            return False

        conn = get_connection()
        cur = conn.cursor()

        # check duplication
        cur.execute(
            "SELECT AttendanceID FROM attendance WHERE StudentID=%s AND StudyID=%s",
            (student_id, study_id)
        )

        if cur.fetchone():
            cur.close()
            conn.close()
            return True

        # Insert
        cur.execute("""
            INSERT INTO attendance (StudyID, StudentID, CheckInTime, Similarity, RealConf)
            VALUES (%s, %s, NOW(), %s, %s)
        """, (study_id, student_id, similarity, real_conf))

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        print('save_attendance error', e)
        return False
