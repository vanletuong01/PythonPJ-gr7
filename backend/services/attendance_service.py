# backend/services/attendance_service.py

from datetime import datetime
from fastapi import UploadFile, HTTPException
import os
import cv2

from backend.db.repositories.attendent_repo import AttendanceRepository
from backend.db.repositories.embeddings_repo import EmbeddingRepository
# ⚠️ Nếu bạn chưa có student_repo.py, ta tạm thời bỏ qua import này
# from backend.db.repositories.student_repo import StudentRepository

from backend.core.face_app.smart_face_attendance import SmartFaceAttendance
from backend.db.config import CONFIDENCE_THRESHOLD


class AttendanceService:
    """Service xử lý logic điểm danh, gọi xuống repository."""

    def __init__(self):
        self.face_att = SmartFaceAttendance(threshold_cosine=CONFIDENCE_THRESHOLD)
        self.repo_att = AttendanceRepository()
        self.repo_emb = EmbeddingRepository()
        # self.repo_stu = StudentRepository()  # nếu sau này có file student_repo thì bật lại

    # ================================================================
    # 1️⃣ Xử lý điểm danh từ ảnh upload
    # ================================================================
    async def mark_attendance(self, file: UploadFile):
        """Điểm danh từ file ảnh upload (sinh viên)."""
        temp_path = None
        try:
            # 1. Lưu tạm file upload vào disk
            contents = await file.read()
            temp_path = f"temp_upload_{datetime.now().timestamp()}.jpg"
            with open(temp_path, "wb") as f:
                f.write(contents)

            # 2. Nhận diện khuôn mặt trong ảnh
            frame = cv2.imread(temp_path)
            meta, score, face_crop = self.face_att.recognize_face(frame)

            if meta is None:
                raise HTTPException(status_code=400, detail="Không nhận diện được khuôn mặt")

            # ⚙️ meta trả về StudyID thay vì StudentID
            study_id = meta.get("StudyID")  # hoặc meta["StudyID"] nếu chắc chắn có
            if not study_id:
                raise HTTPException(status_code=400, detail="Không tìm thấy StudyID trong metadata")

            print(f"✅ Nhận diện: StudyID={study_id}, độ khớp={score:.3f}")

            # 3. Ghi điểm danh vào CSDL + lưu ảnh
            # Chuyển face_crop (RGB) sang BGR để lưu bằng cv2
            face_crop_bgr = cv2.cvtColor(face_crop, cv2.COLOR_RGB2BGR) if face_crop is not None else None
            ok = self.face_att.save_attendance_to_db(study_id=study_id, face_image=face_crop_bgr)

            if not ok:
                raise HTTPException(status_code=500, detail="Ghi điểm danh thất bại")

            return {
                "message": "Điểm danh thành công",
                "study_id": study_id,
                "similarity": round(score, 3)
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Lỗi mark_attendance: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # 4. Xóa file tạm sau khi xử lý
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
