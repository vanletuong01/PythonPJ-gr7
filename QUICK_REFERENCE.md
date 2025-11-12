"""
QUICK REFERENCE CARD - Production Architecture
Paste this in your editor for quick lookup
"""

# ============================================================================
# IMPORTS QUICK REFERENCE
# ============================================================================

# Configuration (read from .env)
from core.config import settings
settings.db.host, settings.db.port, settings.api.port, settings.models.confidence_threshold

# Logging (structured JSON)
from core.logger import get_logger
logger = get_logger(__name__)
logger.info("message")
logger.warning("warning")
logger.error("error", exc_info=True)

# Exceptions (consistent error responses)
from core.exceptions import (
    ValidationException,      # 422 - Invalid input
    NotFoundException,        # 404 - Resource not found
    UnauthorizedException,    # 401 - Auth failed
    DatabaseException,        # 500 - DB error
    ExternalServiceException, # 503 - External API error
    RateLimitException        # 429 - Rate limited
)

# Repositories (data access layer)
from db.repositories import (
    StudentRepository,
    EmbeddingRepository,
    AttendanceRepository
)

# Services (business logic)
from services.embedding_service import EmbeddingService

# Schemas (validation + docs)
from app.schemas import (
    StudentResponse,
    FaceCheckResponse,
    SuccessResponse,
    ErrorResponse
)


# ============================================================================
# CODE PATTERNS
# ============================================================================

## Pattern 1: Route with Validation + Error Handling

```python
from fastapi import APIRouter
from core.logger import get_logger
from core.exceptions import ValidationException, NotFoundException, DatabaseException
from app.schemas import MyRequest, SuccessResponse
from db.repositories.attendent_repo import StudentRepository

logger = get_logger(__name__)
router = APIRouter(prefix="/api/my", tags=["My"])
student_repo = StudentRepository()


@router.post("/endpoint", response_model=SuccessResponse)
async def my_endpoint(request: MyRequest):
    logger.info(f"Processing {request.field}")

    try:
        # Validation using custom exception
        if len(request.field) < 3:
            raise ValidationException("Too short", field="field")

        # Database query using repository
        student = student_repo.get_student_by_code(request.field)
        if not student:
            raise NotFoundException("Student not found")

        # Success response
        return SuccessResponse(
            data={"student": student},
            message="Success"
        )

    except (ValidationException, NotFoundException):
        raise  # Exception handler converts to JSON
    except Exception as e:
        logger.error(f"Failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Operation failed: {str(e)}")
```

## Pattern 2: Repository Data Access

```python
from db.repositories.attendent_repo import StudentRepository
from core.logger import get_logger

logger = get_logger(__name__)
repo = StudentRepository()

# Get student by code
student = repo.get_student_by_code("SV001")

# Get student by ID
student = repo.get_student_by_id(123)

# Create new student
new_student = {
    "code": "SV002",
    "full_name": "John Doe",
    "email": "john@example.com"
}
result = repo.create_student(new_student)

# Update student
repo.update_student_photo_status(123, "completed")
```

## Pattern 3: Service Business Logic
```python
from services.embedding_service import EmbeddingService
from core.logger import get_logger

logger = get_logger(__name__)
service = EmbeddingService()

# Extract embedding from image
embedding = service.extract_embedding_from_image("path/to/image.jpg")

# Extract from folder
embeddings = service.extract_embeddings_from_folder("path/to/folder/")

# Compute average
avg_embedding = service.compute_average_embedding("path/to/folder/")

# Load all embeddings
known_embeddings, metadata = service.load_all_known_embeddings()

# Find best match
best_id, distance, confidence = service.find_best_match(
    unknown_embedding,
    known_embeddings,
    threshold=0.6
)
```

## Pattern 4: Logging Best Practices
```python
from core.logger import get_logger

logger = get_logger(__name__)

# Info level - Important events
logger.info(f"User {user_id} logged in")
logger.info("Processing started")

# Warning level - Potential issues
logger.warning(f"No match found for student {code}")
logger.warning("Attendance already recorded today")

# Error level - Errors with stack trace
logger.error(f"Database query failed: {str(e)}", exc_info=True)
logger.error("Face detection failed", exc_info=True)

# Debug level - For development (set in .env: LOG_LEVEL=DEBUG)
logger.debug(f"Embeddings shape: {embeddings.shape}")
logger.debug(f"Distance: {distance:.4f}")
```


# ============================================================================
# CONFIGURATION REFERENCE
# ============================================================================

## Read from settings
from core.config import settings

# Database settings
settings.db.host           # "localhost"
settings.db.port           # 3306
settings.db.user           # "root"
settings.db.password       # from .env
settings.db.database       # "attendance_db"

# API settings
settings.api.host          # "0.0.0.0"
settings.api.port          # 8000
settings.api.debug         # False (production)
settings.api.title         # "Attendance System API"
settings.api.version       # "2.0.0"

# Model settings
settings.models.confidence_threshold  # 0.6
settings.models.embedding_dim         # 512
settings.models.max_face_distance     # 1.0
settings.models.face_size             # 112

# File settings
settings.files.upload_dir              # "./uploads"
settings.files.student_images_dir      # "./uploads/student_images"
settings.files.max_file_size           # 10 (MB)

# JWT settings
settings.jwt.secret_key                # from .env (never commit!)
settings.jwt.algorithm                 # "HS256"
settings.jwt.access_token_expire_minutes  # 30

# Redis settings
settings.redis.enabled                 # False
settings.redis.host                    # "localhost"
settings.redis.port                    # 6379

# Logging settings
settings.logs.level                    # "INFO"
settings.logs.format                   # "json"


# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

## Raise ValidationException (400 → 422)
from core.exceptions import ValidationException

raise ValidationException(
    "Email already exists",
    field="email",
    value=request.email
)
# Response: {"error": {"code": "VALIDATION_ERROR", "message": "Email already exists", "field": "email"}, "status_code": 422}

## Raise NotFoundException (404)
from core.exceptions import NotFoundException

raise NotFoundException(
    "Student SV001 not found",
    details={"student_code": "SV001"}
)
# Response: {"error": {"code": "NOT_FOUND", "message": "Student SV001 not found"}, "status_code": 404}

## Raise DatabaseException (500)
from core.exceptions import DatabaseException

raise DatabaseException(
    "Failed to save student",
    details={"operation": "insert_student"}
)
# Response: {"error": {"code": "INTERNAL_ERROR", "message": "Failed to save student"}, "status_code": 500}

## Raise UnauthorizedException (401)
from core.exceptions import UnauthorizedException

raise UnauthorizedException("Invalid credentials")
# Response: {"error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}, "status_code": 401}


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

# Liveness probe (is service running?)
GET /health/live → 200 OK

# Readiness probe (is service ready to handle requests?)
GET /health/ready → 200 OK (DB connected, disk space OK)
                 → 503 SERVICE_UNAVAILABLE (DB down, disk full)

# Full health check (detailed status)
GET /health → 200 OK with:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "checks": {
    "database": {"status": "ok", "response_time_ms": 2},
    "cpu": {"percent": 45, "status": "ok"},
    "memory": {"percent": 60, "status": "ok"},
    "disk": {"percent": 70, "status": "ok"}
  }
}


# ============================================================================
# COMMON OPERATIONS
# ============================================================================

## Get student and handle errors
from db.repositories import StudentRepository
from core.exceptions import NotFoundException

repo = StudentRepository()
student = repo.get_student_by_code("SV001")
if not student:
    raise NotFoundException("Student not found")

## Extract embedding with error handling
from services.embedding_service import EmbeddingService
from core.exceptions import ValidationException

service = EmbeddingService()
embedding = service.extract_embedding_from_image("image.jpg")
if embedding is None:
    raise ValidationException("No face detected in image")

## Record attendance
from db.repositories import AttendanceRepository
from core.logger import get_logger

logger = get_logger(__name__)
repo = AttendanceRepository()

study_id = repo.get_study_id_by_student_id(123)
if study_id:
    repo.insert_attendance(
        student_id=123,
        study_id=study_id,
        distance=0.25,
        embedding_used=True
    )
    logger.info("Attendance recorded for student 123")

## Check for duplicate attendance today
from db.repositories import AttendanceRepository

repo = AttendanceRepository()
already_attended = repo.check_already_attended_today(123)
if already_attended:
    logger.warning("Student 123 already attended today")
    return {"message": "Already attended"}


# ============================================================================
# TESTING LOCALLY
# ============================================================================

## Start backend
cd d:\PythonPJ
python backend/main.py

## Test endpoint in curl
curl -X POST http://localhost:8000/api/face/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "student_code=SV001&full_name=John Doe"

## Test health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health

## View API documentation
# Open browser: http://localhost:8000/api/docs
# Try requests directly in Swagger UI


# ============================================================================
# DEBUGGING TIPS
# ============================================================================

## Enable debug logging
# In .env: LOG_LEVEL=DEBUG
# Then: from core.logger import get_logger
#       logger = get_logger(__name__)
#       logger.debug(f"Variable value: {value}")

## Check what's in request
@router.post("/debug")
async def debug(request: Request):
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request body: {await request.body()}")
    return {"ok": True}

## Trace database queries
from db.repositories import StudentRepository
repo = StudentRepository()
logger.debug(f"Getting student by code: SV001")
student = repo.get_student_by_code("SV001")
logger.debug(f"Result: {student}")

## Monitor dependencies
curl -c http://localhost:8000/health/ready
# Check each component status

## Inspect Pydantic validation errors
from app.schemas import MyRequest
try:
    req = MyRequest(field="invalid")
except ValidationError as e:
    logger.error(f"Validation error: {e.json()}")
    # Shows which fields failed and why


# ============================================================================
# FILE LOCATIONS QUICK LOOKUP
# ============================================================================

Configuration    → backend/core/config.py
Logging         → backend/core/logger.py
Exceptions      → backend/core/exceptions.py
Health checks   → backend/api/health_routes.py
Schemas         → backend/app/schemas.py
Repositories    → backend/db/repositories.py
Services        → backend/services/embedding_service.py
Main entry      → backend/main.py
Environment     → .env (from .env.example)

Guides:
  Setup         → INTEGRATION_GUIDE.md
  Migration     → ROUTE_MIGRATION_GUIDE.md
  Summary       → PRODUCTION_SETUP_SUMMARY.md


# ============================================================================
# DOCKER DEPLOYMENT QUICK REFERENCE
# ============================================================================

## Build Docker image
docker build -t attendance-system:1.0.0 .

## Run with docker-compose
docker-compose up -d

## Check logs
docker-compose logs -f backend

## Stop services
docker-compose down

## Rebuild after code changes
docker-compose up -d --build

## Execute command in container
docker-compose exec backend python -c "from backend.core.config import settings; print(settings)"

## Test health in container
docker-compose exec backend curl http://localhost:8000/health/ready


# ============================================================================
# ENVIRONMENT VARIABLES (.env) TEMPLATE
# ============================================================================

ENVIRONMENT=production
DEBUG=false

# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=secure_password_here
DB_DATABASE=attendance_db
DB_PORT=3306

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_TITLE=Attendance System API
API_VERSION=2.0.0

# JWT (Generate: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=your_super_secret_key_at_least_32_chars_generated_randomly
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Files
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=./uploads

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0


# ============================================================================
# PERFORMANCE TIPS
# ============================================================================

1. Use connection pooling (mysql.connector has built-in)
2. Cache embeddings in memory (reduce DB queries)
3. Use Redis for session storage (if enabled)
4. Batch API requests (if possible)
5. Use async/await (FastAPI handles this)
6. Monitor CPU/Memory in /health endpoint
7. Set appropriate JWT token expiry (30 min recommended)
8. Use indexing on student_code, student_id in database
9. Compress embeddings if stored (512 floats = ~2KB)
10. Profile slow queries with logging timestamps


# ============================================================================
# PRODUCTION CHECKLIST (Before Deploy)
# ============================================================================

□ .env file created with secure values
□ JWT_SECRET_KEY is random 32+ chars (not default)
□ DEBUG=false in .env
□ Database credentials correct and secure
□ CORS_ORIGINS set to actual domain (not "*")
□ Health checks pass: curl http://localhost:8000/health/ready
□ All tests pass: pytest backend/tests/
□ Logs are JSON format: grep '"level"' app.log
□ Docker image builds: docker build -t app:1.0.0 .
□ docker-compose.yml reviewed and tested
□ Secrets not in git: .env in .gitignore
□ Database backups configured
□ Monitoring/alerting set up
□ SSL/TLS certificates ready
□ Load testing done (if needed)
□ Error responses are consistent
□ Rate limiting configured
□ Request logging configured
□ Response times acceptable
□ Memory usage stable
□ No N+1 queries
□ All external service calls have timeout

# ============================================================================
