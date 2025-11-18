import cv2
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.ai.face.arcface_embedder import ArcFaceEmbedder
from backend.app.crud.student_embedding import load_all_embeddings
from backend.app.ai.fake_detector import fake_detector_instance   # bạn sẽ load instance có sẵn
from backend.app.ai.detect_face import detect_faces_rgb, extract_face_region_rgb


embedder = ArcfaceEmbedder()
_known = load_all_embeddings()


def match_image_and_check_real(image_np_bgr):
    """
    image_np_bgr: frame BGR từ webcam
    return: dict chứa similarity, real_conf, student...
    """

    # ==========================================
    # 1. Detect face
    # ==========================================
    rgb = cv2.cvtColor(image_np_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)

    boxes, probs = detect_faces_rgb(pil)
    if boxes is None or len(boxes) == 0:
        return {'status': 'no_face'}

    # Lấy mặt lớn nhất
    idx = np.argmax([(b[2] - b[0]) * (b[3] - b[1]) for b in boxes])
    box = boxes[idx]

    face_rgb = extract_face_region_rgb(rgb, box)
    if face_rgb is None:
        return {'status': 'error'}

    # ⚠️ Convert về BGR trước khi embed (vì ArcfaceEmbedder dùng BGR)
    face_bgr = face_rgb[:, :, ::-1]

    # ==========================================
    # 2. ArcFace embedding
    # ==========================================
    emb = embedder.get_embedding(face_bgr)
    if emb is None:
        return {'status': 'embed_fail'}

    # ==========================================
    # 3. Load DB embedding
    # ==========================================
    global _known
    if _known["encodings"].size == 0:
        _known = load_all_embeddings()
        if _known["encodings"].size == 0:
            return {"status": "no_db"}

    sims = cosine_similarity([emb], _known["encodings"])[0]
    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])
    student = _known["meta"][best_idx]

    # ==========================================
    # 4. Fake detector (real vs fake)
    # ==========================================
    fake_result = fake_detector_instance.process_frame(image_np_bgr)
    real_conf_fake = fake_result["real_conf"]  # [0..1]

    # ==========================================
    # 5. Tính tổng real_conf (kết hợp nhận diện + fake)
    # ==========================================
    real_conf = 0.6 * best_score + 0.4 * real_conf_fake

    return {
        "status": "ok",
        "found": best_score >= 0.55,
        "similarity": best_score,
        "student": student,
        "is_real": real_conf >= 0.55,
        "real_conf": real_conf,
        "fake_score": fake_result["real_conf"],   # giữ format cũ
        "debug": {
            "emb_sim": best_score,
            "fake_real_conf": real_conf_fake
        }
    }
