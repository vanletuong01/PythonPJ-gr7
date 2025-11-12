"""
Integration Guide - Production-Grade Architecture
Hướng dẫn setup + integration toàn bộ hệ thống
"""

# ============================================================================
# PHASE 1: FOUNDATION SETUP (Completed ✅)
# ============================================================================

## 1. Environment Configuration (.env file)
```
# Copy từ .env.example
cp .env.example .env

# Edit .env với giá trị thực
ENVIRONMENT=production
DEBUG=false

# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_secure_password
DB_DATABASE=attendance_db
DB_PORT=3306

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_TITLE="Attendance System API"
API_VERSION="2.0.0"
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# JWT Security
JWT_SECRET_KEY=your_super_secret_key_at_least_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional, for caching)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# File uploads
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=./uploads
```

## 2. Infrastructure Files Created
✅ `backend/core/config.py`
   - Pydantic BaseSettings singleton
   - 8 configuration classes (Database, API, Models, Files, JWT, Redis, Logs)
   - Environment variable override support
   - Validators for production-safe values

✅ `backend/core/logger.py`
   - JSON structured logging
   - JSONFormatter class
   - setup_logging() function
   - get_logger() helper
   - Fields: timestamp, level, logger, message, module, function, line, request_id, error_code

✅ `backend/core/exceptions.py`
   - AppException base class
   - 11 custom exception subclasses
   - create_error_response() factory
   - setup_exception_handlers() function
   - Global error handling middleware

✅ `backend/api/health_routes.py`
   - GET /health - Detailed health check
   - GET /health/live - Liveness probe (Kubernetes)
   - GET /health/ready - Readiness probe (Kubernetes)
   - Checks: Database, CPU, Memory, Disk Space

✅ `backend/app/schemas.py`
   - 25+ Pydantic models for validation
   - Request/Response schemas
   - Error schemas
   - Pagination schemas
   - Type hints for all API inputs/outputs

✅ `backend/main.py` (Updated)
   - Integrated config, logger, exceptions
   - Health check router registered
   - Request ID middleware for tracing
   - Production-grade startup/shutdown events
   - Logging for all lifecycle events


# ============================================================================
# PHASE 2: MIGRATION CHECKLIST
# ============================================================================

## Step 1: Update API Routes to Use New Exception Handling

Before (Old Code):
```python
from fastapi import APIRouter
from db.database import get_connection

router = APIRouter(prefix="/api/face", tags=["Face"])

@router.post("/register")
async def register_face(student_code: str, image: UploadFile):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Direct SQL query...
    except Exception as e:
        return {"error": str(e)}  # Raw exception
```

After (New Code):

```python
from fastapi import APIRouter
from core.logger import get_logger
from core.exceptions import ValidationException, DatabaseException
from app.schemas import FaceRegisterRequest, SuccessResponse
from db.repositories.attendent_repo import StudentRepository, EmbeddingRepository
from services.embedding_service import EmbeddingService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/face", tags=["Face"])


@router.post("/register")
async def register_face(request: FaceRegisterRequest):  # Pydantic validation
    logger.info(f"Registering face for student: {request.student_code}")

    try:
        student_repo = StudentRepository()

        # Validation using exception
        student = student_repo.get_student_by_code(request.student_code)
        if not student:
            raise ValidationException("Student not found", field="student_code")

        # Success response
        return SuccessResponse(
            data={"student_id": student["id"]},
            message="Face registration started"
        )

    except ValidationException:
        raise  # Auto-converted to JSON response by exception handler
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to register: {str(e)}")
```

Exception Handler automatically converts to:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Student not found",
    "field": "student_code"
  },
  "timestamp": "2024-01-15T10:30:45.123456",
  "request_id": "req-12345",
  "status_code": 422
}
```

## Step 2: Refactor Routes to Use Repositories + Services

File: `backend/api/face_routes.py`

```python
from fastapi import APIRouter, UploadFile, File
from core.logger import get_logger
from core.exceptions import ValidationException, NotFoundException, DatabaseException
from app.schemas import (
    FaceRegisterRequest, FaceFinalizeRequest, FaceCheckRequest,
    FaceCheckResponse, SuccessResponse
)
from db.repositories.attendent_repo import StudentRepository, EmbeddingRepository, AttendanceRepository
from services.embedding_service import EmbeddingService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/face", tags=["Face"])

# Instantiate repositories and services
student_repo = StudentRepository()
embedding_repo = EmbeddingRepository()
attendance_repo = AttendanceRepository()
embedding_service = EmbeddingService()


@router.post("/register")
async def register_face(request: FaceRegisterRequest):
    """Start face registration session"""
    logger.info(f"Starting face registration for {request.student_code}")

    try:
        # Validate student exists
        student = student_repo.get_student_by_code(request.student_code)
        if not student:
            raise NotFoundException(
                f"Student with code {request.student_code} not found",
                details={"student_code": request.student_code}
            )

        # Update student photo status
        student_repo.update_student_photo_status(student["id"], "processing")

        logger.info(f"Face registration started for student {student['id']}")
        return SuccessResponse(
            data={
                "student_id": student["id"],
                "student_code": student["code"],
                "full_name": student["full_name"]
            },
            message="Face registration session created"
        )

    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Face registration failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to start face registration: {str(e)}")


@router.post("/finalize")
async def finalize_face(request: FaceFinalizeRequest):
    """Finalize face registration and compute embeddings"""
    logger.info(f"Finalizing face registration for {request.student_code}")

    try:
        # Get student
        student = student_repo.get_student_by_code(request.student_code)
        if not student:
            raise NotFoundException(f"Student {request.student_code} not found")

        student_id = student["id"]

        # Get all uploaded images from file system
        image_dir = f"{settings.files.student_images_dir}/{student_id}"
        if not os.path.exists(image_dir):
            raise ValidationException("No images found for this student")

        # Compute average embedding
        embedding = embedding_service.compute_average_embedding(image_dir)

        if embedding is None:
            raise ValidationException("Failed to extract face embeddings from images")

        # Save to database
        embedding_repo.insert_or_update_embedding(
            student_id=student_id,
            embedding=embedding,
            dimensions=len(embedding)
        )

        # Update student status
        student_repo.update_student_photo_status(student_id, "completed")

        logger.info(f"Face registration completed for student {student_id}")
        return SuccessResponse(
            data={
                "student_id": student_id,
                "embedding_dimensions": len(embedding),
                "status": "completed"
            },
            message="Face registration finalized successfully"
        )

    except (NotFoundException, ValidationException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Finalize failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to finalize registration: {str(e)}")


@router.post("/check", response_model=FaceCheckResponse)
async def check_face(request: FaceCheckRequest):
    """Recognize face and record attendance"""
    logger.info("Checking face for attendance")

    try:
        # Download/load image
        if request.image_url:
            image = embedding_service.download_image(request.image_url)
        else:
            raise ValidationException("image_url required")

        # Extract embedding
        unknown_embedding = embedding_service.extract_embedding_from_image(image)
        if unknown_embedding is None:
            raise ValidationException("No face detected in image")

        # Load all known embeddings
        known_embeddings, students_data = embedding_service.load_all_known_embeddings()

        # Find best match
        matched_student_id, distance, confidence = embedding_service.find_best_match(
            unknown_embedding,
            known_embeddings,
            threshold=settings.models.confidence_threshold
        )

        if matched_student_id is None:
            logger.warning(f"No match found. Best distance: {distance}")
            return FaceCheckResponse(
                matched=False,
                timestamp=datetime.utcnow(),
                distance=distance,
                confidence=1 - (distance / 2),  # Convert distance to confidence
                debug_info={"message": "No student matched"}
            )

        # Get matched student
        student = student_repo.get_student_by_id(matched_student_id)
        if not student:
            logger.error(f"Student {matched_student_id} not found in DB")
            raise NotFoundException(f"Student {matched_student_id} not found")

        # Check if already attended today
        today_attendance = attendance_repo.check_already_attended_today(matched_student_id)
        if today_attendance:
            logger.warning(f"Student {student['code']} already attended today")
            return FaceCheckResponse(
                matched=True,
                student_code=student["code"],
                full_name=student["full_name"],
                confidence=1 - (distance / 2),
                distance=distance,
                timestamp=datetime.utcnow(),
                debug_info={"message": "Already attended today"}
            )

        # Record attendance
        study_id = attendance_repo.get_study_id_by_student_id(matched_student_id)
        if study_id:
            attendance_repo.insert_attendance(
                student_id=matched_student_id,
                study_id=study_id,
                distance=distance,
                embedding_used=True
            )
            logger.info(f"Attendance recorded for {student['code']}")

        return FaceCheckResponse(
            matched=True,
            student_code=student["code"],
            full_name=student["full_name"],
            confidence=1 - (distance / 2),
            distance=distance,
            timestamp=datetime.utcnow()
        )

    except (NotFoundException, ValidationException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Face check failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to check face: {str(e)}")
```

## Step 3: Update Other Route Handlers Similarly

Apply same pattern to:
- `backend/api/auth_routes.py` - Add validation schemas, error handling
- `backend/api/student_routes.py` - Use StudentRepository
- `backend/api/attendance_routes.py` - Use AttendanceRepository
- `backend/api/stats_routes.py` - Use repositories for queries


# ============================================================================
# PHASE 3: TESTING COMMANDS
# ============================================================================

## 1. Verify Imports Work
```bash
cd d:\PythonPJ
python -c "from backend.core.config import settings; print('✅ Config OK')"
python -c "from backend.core.logger import get_logger; print('✅ Logger OK')"
python -c "from backend.core.exceptions import AppException; print('✅ Exceptions OK')"
```

## 2. Start Backend Server
```bash
cd d:\PythonPJ
python backend/main.py
# OR
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Liveness
curl http://localhost:8000/health/live

# Readiness
curl http://localhost:8000/health/ready

# API docs
# Open browser: http://localhost:8000/api/docs
```

## 4. Test Exception Handling
```bash
# Try invalid request (should get JSON error response)
curl -X POST http://localhost:8000/api/face/register \
  -H "Content-Type: application/json" \
  -d '{"student_code":""}'

# Response:
# {
#   "error": {
#     "code": "VALIDATION_ERROR",
#     "message": "..."
#   },
#   "timestamp": "2024-01-15T...",
#   "status_code": 422
# }
```


# ============================================================================
# PHASE 4: DOCKER DEPLOYMENT (Next Phase)
# ============================================================================

Upcoming files:
- Dockerfile (backend)
- Dockerfile (frontend)
- docker-compose.yml
- .dockerignore
- nginx.conf (reverse proxy)


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

Foundation Setup:
✅ Config management (environment variables + Pydantic)
✅ Structured logging (JSON format + LoggerAdapter)
✅ Exception handling (custom exceptions + global middleware)
✅ Health checks (liveness/readiness probes)
✅ API validation (Pydantic schemas + auto docs)
✅ main.py integration

Route Migration:
⬜ Update face_routes.py to use repositories/services
⬜ Update auth_routes.py to use ValidationException
⬜ Update student_routes.py to use StudentRepository
⬜ Update attendance_routes.py to use AttendanceRepository
⬜ Add Pydantic schemas to all endpoints

Testing:
⬜ Unit tests for repositories
⬜ Unit tests for services
⬜ Integration tests for API endpoints
⬜ Load testing for performance

Deployment:
⬜ Docker files + compose setup
⬜ Environment variable templates
⬜ Database migration scripts
⬜ CI/CD pipeline (GitHub Actions)


# ============================================================================
# PRODUCTION CHECKLIST
# ============================================================================

Before deploying to production:
☐ All environment variables set in .env (never commit secrets)
☐ JWT_SECRET_KEY changed to random 32+ chars
☐ DEBUG=false in production
☐ Database password strong and secure
☐ CORS_ORIGINS set to exact domain (not ["*"])
☐ Health checks passing (/health/ready returns 200)
☐ Logs configured as JSON for ELK/Splunk
☐ Error responses are consistent (check /docs)
☐ Database backups configured
☐ Redis cache enabled (if available)
☐ Rate limiting configured
☐ HTTPS/TLS enabled
☐ Docker images built and pushed to registry
☐ Kubernetes deployments ready
☐ Monitoring/alerting configured

# ============================================================================
