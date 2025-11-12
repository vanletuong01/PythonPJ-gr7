import os
import cv2
import torch
import numpy as np
from PIL import Image
from datetime import datetime
from pathlib import Path
from facenet_pytorch import MTCNN
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity

from backend.db.repositories.embeddings_repo import EmbeddingRepository
from backend.db.repositories.attendent_repo import AttendanceRepository
from backend.core.face_app.load_embeddings import extract_face_embedding
from backend.core.logger import get_logger
from backend.db.config import ATTENDANCE_IMAGES_DIR

logger = get_logger(__name__)


class SmartFaceAttendance:
    """
    Lớp xử lý logic nhận diện khuôn mặt và điểm danh.
    - Dùng ArcFace + MTCNN.
    - Dùng Repository để truy xuất database.
    """

    def __init__(self, threshold_cosine=0.45):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.threshold_cosine = threshold_cosine

        print("🚀 Load ArcFace model...")
        self.arcface_model = DeepFace.build_model("ArcFace")
        self.mtcnn = MTCNN(image_size=112, margin=10, keep_all=True, device=self.device)
        print("✅ ArcFace sẵn sàng!")

        # Repository
        self.embedding_repo = EmbeddingRepository()
        self.attendance_repo = AttendanceRepository()

        # Cache embeddings
        self.known_faces = self.load_faces_from_mysql()

    # =====================================================
    # 1️⃣ LOAD EMBEDDINGS TỪ DATABASE
    # =====================================================
    def load_faces_from_mysql(self):
        """Tải toàn bộ embedding sinh viên từ MySQL."""
        try:
            logger.info("Loading embeddings from database...")
            embeddings, meta = self.embedding_repo.get_all_embeddings()

            if embeddings.size == 0:
                logger.warning("No valid embeddings found in database")
                return {"ids": [], "encodings": np.array([], dtype=np.float32), "meta": []}

            ids = [str(m["StudyID"]) for m in meta]  # ⚠️ dùng StudyID thay vì StudentID
            logger.info(f"✅ Loaded {len(ids)} embeddings (shape={embeddings.shape})")

            return {"ids": ids, "encodings": embeddings, "meta": meta}

        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}", exc_info=True)
            return {"ids": [], "encodings": np.array([], dtype=np.float32), "meta": []}

    # =====================================================
    # 2️⃣ SINH EMBEDDING MỚI TỪ ẢNH
    # =====================================================
    def get_embedding(self, face_img):
        """Sinh embedding từ ảnh khuôn mặt cắt."""
        try:
            temp_path = "temp_face.jpg"
            Image.fromarray(face_img.astype(np.uint8)).save(temp_path)
            emb = extract_face_embedding(temp_path)
            os.remove(temp_path)

            if emb is not None:
                emb = emb / (np.linalg.norm(emb) + 1e-9)
            return emb
        except Exception as e:
            logger.error(f"Lỗi sinh embedding: {e}")
            return None

    # =====================================================
    # 3️⃣ NHẬN DIỆN KHUÔN MẶT TRONG ẢNH / FRAME
    # =====================================================
    def recognize_face(self, frame):
        """Phát hiện và so khớp khuôn mặt với database."""
        if self.known_faces["encodings"].size == 0:
            logger.warning("⚠️ Không có embedding nào để so khớp.")
            return None, None, None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes, probs = self.mtcnn.detect(Image.fromarray(rgb))

        if boxes is None or len(boxes) == 0:
            return None, None, None

        # chọn khuôn mặt lớn nhất
        idx = np.argmax([(b[2] - b[0]) * (b[3] - b[1]) for b in boxes])
        x1, y1, x2, y2 = boxes[idx].astype(int)
        face_crop = rgb[y1:y2, x1:x2]

        if face_crop.size == 0:
            return None, None, None

        emb = self.get_embedding(face_crop)
        if emb is None:
            return None, None, None

        sims = cosine_similarity([emb], self.known_faces["encodings"])[0]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        meta = self.known_faces["meta"][best_idx]

        if best_score < self.threshold_cosine:
            logger.info(f"❌ Không khớp (score={best_score:.3f})")
            return None, best_score, None

        return meta, best_score, face_crop


    # =====================================================
    # 4️⃣ GHI KẾT QUẢ ĐIỂM DANH
    def save_attendance_to_db(self, study_id, face_image=None):
        """Lưu kết quả điểm danh bằng StudyID + ảnh thực tế."""
        try:
            if self.attendance_repo.check_already_attended_today(study_id):
                logger.warning(f"StudyID {study_id} already attended today")
                return False

            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_studyid_{study_id}_{timestamp}.jpg"
            
            # Đảm bảo thư mục tồn tại
            Path(ATTENDANCE_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
            
            # Lưu ảnh nếu có
            photo_path = None
            if face_image is not None:
                photo_path = os.path.join(ATTENDANCE_IMAGES_DIR, filename)
                cv2.imwrite(photo_path, face_image)
                logger.info(f"✅ Lưu ảnh điểm danh: {photo_path}")
                # Lưu đường dẫn tương đối vào DB
                photo_path = os.path.relpath(photo_path, os.getcwd())
            
            success = self.attendance_repo.insert_attendance(
                study_id=study_id,
                photo_path=photo_path
            )
            
            if success:
                logger.info(f"✅ Điểm danh ghi vào DB: StudyID={study_id}")
            
            return success

        except Exception as e:
            logger.error(f"Error recording attendance: {e}", exc_info=True)
            return False
