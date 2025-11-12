"""
Face Recognition Routes - Refactored with New Architecture
Using: Repositories, Services, Schemas, Exception Handling
"""
from fastapi import APIRouter, UploadFile, Form, Query, File
import os
from datetime import datetime

# Core infrastructure
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.exceptions import (
    ValidationException,
    NotFoundException,
    DatabaseException
)

# Schemas for validation
from backend.app.schemas import (
    FaceCheckResponse,
    SuccessResponse
)

# Database & Services
# IMPORT CHÍNH XÁC: mỗi repo nằm trong file tương ứng
from backend.db.repositories.student_repo import StudentRepository
from backend.db.repositories.embeddings_repo import EmbeddingRepository
from backend.db.repositories.attendent_repo import AttendanceRepository

from backend.services.embedding_service import EmbeddingService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/face", tags=["Face Recognition"])

# Initialize repositories and services
student_repo = StudentRepository()
embedding_repo = EmbeddingRepository()
attendance_repo = AttendanceRepository()
embedding_service = EmbeddingService()

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = settings.files.student_images_dir
os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# 1️⃣ API: Bắt đầu đăng ký khuôn mặt (tạo session)
# =========================================================
@router.post("/register")
async def register_face_session(
    student_code: str = Form(...),
    full_name: str = Form(...)
):
    logger.info(f"Starting face registration session for {student_code}")

    try:
        if not student_code or not student_code.strip():
            raise ValidationException("Student code cannot be empty", field="student_code")

        if not full_name or not full_name.strip():
            raise ValidationException("Full name cannot be empty", field="full_name")

        student = student_repo.get_student_by_code(student_code)
        if not student:
            logger.warning(f"Student {student_code} not found")
            raise NotFoundException(f"Student with code '{student_code}' not found", details={"student_code": student_code})

        # Student repo returns dict with StudentID key (DB schema). Fall back to 'id' if different.
        student_id = student.get("StudentID") or student.get("id")

        student_repo.update_student_photo_status(student_id, "processing")

        student_folder = os.path.join(DATA_DIR, str(student_id))
        os.makedirs(student_folder, exist_ok=True)

        logger.info(f"Face registration session created for student {student_id}")

        return SuccessResponse(
            data={
                "student_id": student_id,
                "student_code": student_code,
                "full_name": full_name,
                "status": "ready"
            },
            message="Face registration session created. Ready to upload images."
        ).dict()

    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Face registration failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to start face registration: {str(e)}", details={"student_code": student_code})


# =========================================================
# 2️⃣ API: Upload ảnh khuôn mặt
# =========================================================
@router.post("/upload-frame")
async def upload_face_frame(
    student_code: str = Form(...),
    index: int = Form(...),
    photo: UploadFile = File(...)
):
    logger.info(f"Uploading frame {index} for student {student_code}")

    try:
        if index < 0 or index > 24:
            raise ValidationException("Frame index must be 0-24", field="index")

        if not photo.filename:
            raise ValidationException("No file provided", field="photo")

        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        file_ext = os.path.splitext(photo.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationException(f"File type {file_ext} not allowed. Allowed: {allowed_extensions}", field="photo")

        student = student_repo.get_student_by_code(student_code)
        if not student:
            raise NotFoundException(f"Student {student_code} not found")

        student_id = student.get("StudentID") or student.get("id")

        student_folder = os.path.join(DATA_DIR, str(student_id))
        os.makedirs(student_folder, exist_ok=True)

        save_path = os.path.join(student_folder, f"frame_{index:02d}{file_ext}")

        contents = await photo.read()
        # settings.files.max_file_size is MB in your config; adjust if needed
        if len(contents) > settings.files.max_file_size * 1024 * 1024:
            raise ValidationException(f"File size exceeds {settings.files.max_file_size}MB limit", field="photo")

        with open(save_path, "wb") as f:
            f.write(contents)

        logger.info(f"Frame {index} saved for student {student_id}: {save_path}")

        return SuccessResponse(
            data={
                "student_id": student_id,
                "frame_index": index,
                "saved_path": save_path
            },
            message=f"Frame {index} uploaded successfully"
        ).dict()

    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"Frame upload failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to upload frame: {str(e)}")


# =========================================================
# 3️⃣ API: Hoàn tất đăng ký (tính embedding)
# =========================================================
@router.post("/finalize")
async def finalize_face_registration(
    student_code: str = Query(...),
    full_name: str = Query(...)
):
    logger.info(f"Finalizing face registration for {student_code}")

    try:
        student = student_repo.get_student_by_code(student_code)
        if not student:
            raise NotFoundException(f"Student {student_code} not found")

        student_id = student.get("StudentID") or student.get("id")
        student_folder = os.path.join(DATA_DIR, str(student_id))

        if not os.path.exists(student_folder):
            raise ValidationException("No images found for this student", field="student_code")

        image_files = [
            os.path.join(student_folder, f)
            for f in os.listdir(student_folder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))
        ]

        if not image_files:
            raise ValidationException("No valid images found in student folder")

        logger.info(f"Processing {len(image_files)} images for student {student_id}")

        avg_embedding = embedding_service.compute_average_embedding(student_folder)

        if avg_embedding is None:
            raise ValidationException("Failed to extract face embeddings from images", details={"processed_images": len(image_files)})

        # NOTE: call repository correctly — depending on your EmbeddingRepository API signature.
        # Here we assume insert_or_update_embedding(student_code, embedding, ...) exists.
        # If EmbeddingRepository expects student_id, adapt accordingly.
        embedding_repo.insert_or_update_embedding(
            student_code=student_code,
            embedding=avg_embedding,
            full_name=full_name,
            photo_path=None,
            quality=None,
            source="registration"
        )

        student_repo.update_student_photo_status(student_id, "completed")

        logger.info(f"Face registration completed for student {student_id}. Processed {len(image_files)} images.")

        return SuccessResponse(
            data={
                "student_id": student_id,
                "student_code": student_code,
                "full_name": full_name,
                "images_processed": len(image_files),
                "embedding_dimensions": len(avg_embedding),
                "status": "completed"
            },
            message="Face registration completed successfully"
        ).dict()

    except (ValidationException, NotFoundException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Finalize registration failed: {str(e)}", exc_info=True)
        try:
            student = student_repo.get_student_by_code(student_code)
            if student:
                student_repo.update_student_photo_status(student.get("StudentID") or student.get("id"), "failed")
        except:
            pass
        raise DatabaseException(f"Failed to finalize registration: {str(e)}")


# =========================================================
# 4️⃣ API: Điểm danh (nhận dạng khuôn mặt)
# =========================================================
@router.post("/check", response_model=FaceCheckResponse)
async def check_attendance(
    photo: UploadFile = File(...),
    quality_threshold: float = Query(0.6, ge=0.0, le=1.0),
    return_debug: bool = Query(False)
):
    logger.info("Checking face for attendance")

    temp_path = None
    try:
        # Save temp file
        temp_path = os.path.join(DATA_DIR, f"temp_{datetime.now().timestamp()}.jpg")
        contents = await photo.read()

        if len(contents) > settings.files.max_file_size * 1024 * 1024:
            raise ValidationException(f"File size exceeds {settings.files.max_file_size}MB")

        with open(temp_path, "wb") as f:
            f.write(contents)

        # Extract embedding
        unknown_embedding = embedding_service.extract_embedding_from_image(temp_path)

        if unknown_embedding is None:
            logger.warning("No face detected in uploaded image")
            return FaceCheckResponse(
                matched=False,
                timestamp=datetime.utcnow(),
                debug_info={"message": "No face detected in image"}
            )

        logger.info(f"Extracted embedding. Dimensions: {len(unknown_embedding)}")

        # Load known embeddings
        known_embeddings, students_metadata = embedding_service.load_all_known_embeddings()

        if known_embeddings.size == 0:
            logger.warning("No known embeddings in database")
            return FaceCheckResponse(
                matched=False,
                timestamp=datetime.utcnow(),
                debug_info={"message": "No students in database"}
            )

        # Find best match
        best_student_id, distance, confidence = embedding_service.find_best_match(
            unknown_embedding,
            known_embeddings,
            threshold=quality_threshold
        )

        logger.info(f"Best match distance: {distance:.4f}, confidence: {confidence:.4f}")

        if best_student_id is None:
            logger.warning(f"No match found. Best distance: {distance:.4f}")
            return FaceCheckResponse(
                matched=False,
                distance=distance,
                confidence=confidence,
                timestamp=datetime.utcnow(),
                debug_info={"message": "No student matched confidence threshold"}
            )

        # Get student details
        student = student_repo.get_student_by_id(best_student_id)
        if not student:
            logger.error(f"Student {best_student_id} not found in DB")
            raise NotFoundException(f"Student {best_student_id} not found")

        student_code = student.get("StudentCode") or student.get("code")
        full_name = student.get("FullName") or student.get("full_name")

        logger.info(f"Matched student: {student_code} - {full_name} (confidence: {confidence:.4f})")

        # --- IMPORTANT: use study_id to check/record attendance (attendance table stores StudyID) ---
        study_id = attendance_repo.get_study_id_by_student_id(best_student_id)
        if not study_id:
            logger.warning(f"No study_id found for student {best_student_id}; cannot record attendance.")
            # still return matched but indicate cannot record
            return FaceCheckResponse(
                matched=True,
                student_code=student_code,
                full_name=full_name,
                confidence=confidence,
                distance=distance,
                timestamp=datetime.utcnow(),
                debug_info={"message": "Matched but no study assignment found; attendance not recorded"}
            )

        # Check if already attended today (by study_id)
        already = attendance_repo.check_already_attended_today_by_studyid(study_id)
        if already:
            logger.info(f"Student {student_code} (StudyID={study_id}) already attended today")
            return FaceCheckResponse(
                matched=True,
                student_code=student_code,
                full_name=full_name,
                confidence=confidence,
                distance=distance,
                timestamp=datetime.utcnow(),
                debug_info={"message": "Student already attended today"}
            )

        # Record attendance (only study_id and photo_path)
        try:
            attendance_repo.insert_attendance(study_id=study_id, photo_path=temp_path)
            logger.info(f"Attendance recorded for {student_code} (StudyID={study_id})")
        except Exception as e:
            logger.error(f"Failed to record attendance: {str(e)}", exc_info=True)
            # don't fail the whole flow; still return matched

        return FaceCheckResponse(
            matched=True,
            student_code=student_code,
            full_name=full_name,
            confidence=confidence,
            distance=distance,
            timestamp=datetime.utcnow(),
            debug_info={"message": "Attendance recorded"} if return_debug else None
        )

    except (ValidationException, NotFoundException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Face check failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to check face: {str(e)}")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


# =========================================================
# 5️⃣ API: Test endpoint - kiểm tra tất cả embeddings
# =========================================================
@router.get("/test-embeddings")
async def test_embeddings():
    logger.info("Testing embeddings")

    try:
        known_embeddings, students_metadata = embedding_service.load_all_known_embeddings()

        if known_embeddings.size == 0:
            return {"status": "ok", "message": "No embeddings found", "total_embeddings": 0}

        return {
            "status": "ok",
            "message": "Embeddings loaded successfully",
            "total_embeddings": len(students_metadata),
            "embedding_dimensions": known_embeddings.shape[1] if len(known_embeddings.shape) > 1 else 512,
            "students": [
                {"student_id": m["student_id"], "student_code": m.get("code", "N/A"), "full_name": m.get("full_name", "N/A")}
                for m in students_metadata[:10]
            ],
            "total_in_list": len(students_metadata)
        }

    except Exception as e:
        logger.error(f"Test embeddings failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to test embeddings: {str(e)}")
