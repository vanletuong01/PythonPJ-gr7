"""
Route Migration Guide
How to update existing routes to use new architecture
"""

# ============================================================================
# SECTION 1: Understanding the New Architecture
# ============================================================================

## Pattern Before (Old Code - Anti-patterns)
```python
from fastapi import APIRouter
from db.database import get_connection
import traceback

router = APIRouter(prefix="/api/face")

@router.post("/check")
async def check_face(photo: UploadFile):
    try:
        # ❌ Direct database connection in route handler
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # ❌ SQL query directly in route
        cursor.execute("SELECT * FROM student WHERE StudentID = %s", (123,))
        student = cursor.fetchone()
        
        # ❌ No validation - raw exception responses
        if not student:
            return {"error": "Student not found"}  # Inconsistent format
        
        # ❌ Raw exceptions returned to client
        return {"status": "error", "message": str(e)}
        
    except Exception as e:
        print("❌ Error:", traceback.format_exc())  # No structured logging
        return JSONResponse({"status": "error", "message": str(e)})
    finally:
        cursor.close()  # ❌ Can be missed/forgotten
        conn.close()
```

**Problems:**
- ❌ SQL queries scattered everywhere
- ❌ Cursor management can leak connections
- ❌ No input validation
- ❌ Inconsistent error responses
- ❌ Hard to test (direct DB calls)
- ❌ Business logic mixed with HTTP handling
- ❌ Print statements instead of proper logging
- ❌ No structured error codes


## Pattern After (New Code - Best Practices)

```python
from fastapi import APIRouter
from core.logger import get_logger
from core.exceptions import ValidationException, NotFoundException, DatabaseException
from app.schemas import StudentResponse, SuccessResponse
from db.repositories.attendent_repo import StudentRepository

logger = get_logger(__name__)  # ✅ Structured logging
router = APIRouter(prefix="/api/face")

# ✅ Dependency injection
student_repo = StudentRepository()


@router.post("/check", response_model=SuccessResponse)
async def check_face(photo: UploadFile):
    # ✅ Pydantic validation happens automatically
    # ✅ Proper logging
    logger.info("Checking face for attendance")

    try:
        # ✅ Use repository instead of direct DB
        student = student_repo.get_student_by_id(123)

        # ✅ Explicit validation with custom exception
        if not student:
            raise NotFoundException("Student not found")

        # ✅ Consistent response format
        return SuccessResponse(
            data={"student": student},
            message="Success"
        )

    except (NotFoundException, ValidationException):
        # ✅ Let exception handler format the response
        raise
    except Exception as e:
        # ✅ Structured logging with traceback
        logger.error(f"Check failed: {str(e)}", exc_info=True)
        raise DatabaseException(f"Failed to check: {str(e)}")
```

**Benefits:**
- ✅ SQL queries centralized in Repository
- ✅ Connection management in Repository
- ✅ Input validated via Pydantic
- ✅ Consistent error responses via exception handlers
- ✅ Easy to test (inject mock repository)
- ✅ Separation of concerns
- ✅ Structured JSON logging
- ✅ Defined error codes


# ============================================================================
# SECTION 2: Step-by-Step Migration Example
# ============================================================================

### Before: Old face_routes.py
File: `backend/api/face_routes_old.py` (current file)

### After: New face_routes.py
File: `backend/api/face_routes_refactored.py` (reference implementation)

### Migration Steps:

#### STEP 1: Add new imports

```python
# Old imports to keep:
from fastapi import APIRouter, UploadFile, Form, Query

# New imports to add:
from core.config import settings
from core.logger import get_logger
from core.exceptions import (
    ValidationException,
    NotFoundException,
    DatabaseException
)
from app.schemas import (
    SuccessResponse,
    FaceCheckRequest,
    FaceCheckResponse
)
from db.repositories.attendent_repo import StudentRepository, EmbeddingRepository, AttendanceRepository
from services.embedding_service import EmbeddingService

# Setup
logger = get_logger(__name__)
student_repo = StudentRepository()
embedding_repo = EmbeddingRepository()
attendance_repo = AttendanceRepository()
embedding_service = EmbeddingService()
```

#### STEP 2: Replace direct DB calls with Repository calls

Before:
```python
# ❌ Old way - direct database in route
conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM student WHERE StudentCode = %s", (code,))
student = cursor.fetchone()
cursor.close()
conn.close()
```

After:
```python
# ✅ New way - use repository
student = student_repo.get_student_by_code(student_code)
# Repository handles: connection, cursor, closing, error handling
```

#### STEP 3: Add input validation

Before:
```python
# ❌ Old way - no validation
@router.post("/register")
async def register_frame(
    student_code: str = Form(...),
    photo: UploadFile = None
):
    if not student_code:
        return JSONResponse({"status": "error", "message": "..."})
```

After:
```python
# ✅ New way - use Pydantic schemas
from app.schemas import FaceRegisterRequest

@router.post("/register")
async def register_frame(request: FaceRegisterRequest):
    # Pydantic validates automatically
    # Invalid input → automatic 422 response
    if not request.student_code or not request.full_name:
        raise ValidationException(
            "Student code and name required",
            details={"fields": ["student_code", "full_name"]}
        )
```

#### STEP 4: Replace raw exceptions with custom exceptions

Before:
```python
# ❌ Old way - return raw error
return JSONResponse({"status": "error", "message": str(e)})
```

After:
```python
# ✅ New way - raise custom exception
if not student:
    raise NotFoundException(
        "Student not found",
        details={"student_code": code}
    )

if some_validation_fails:
    raise ValidationException(
        "Validation failed",
        field="field_name"
    )

if database_error:
    raise DatabaseException(
        "Database operation failed"
    )
```

#### STEP 5: Replace direct embedding logic with EmbeddingService

Before:
```python
# ❌ Old way - embedding code scattered everywhere
result = DeepFace.represent(
    img_path=img_path,
    model_name="ArcFace",
    detector_backend="mtcnn",
    enforce_detection=False
)
embeddings.append(result[0]["embedding"])

# ... repeat in 5 different files
```

After:
```python
# ✅ New way - use service
embedding = embedding_service.extract_embedding_from_image(image_path)
embeddings = embedding_service.extract_embeddings_from_folder(folder_path)
avg_embedding = embedding_service.compute_average_embedding(folder_path)
matched_id, distance, conf = embedding_service.find_best_match(embedding, known_embeddings)
```

#### STEP 6: Use logging instead of print

Before:
```python
# ❌ Old way
print("Processing images...")
print("✅ Success")
print("❌ Error:", traceback.format_exc())
```

After:
```python
# ✅ New way
logger.info("Processing images")
logger.info("Success")
logger.error("Error occurred", exc_info=True)  # Includes stack trace
```

#### STEP 7: Return consistent response format

Before:
```python
# ❌ Old way - inconsistent response formats
return {"status": "ok"}
return {"status": "error", "message": "..."}
return {"status": "success", "student": {...}}
return JSONResponse({"status": "not_found", ...})
```

After:
```python
# ✅ New way - consistent SuccessResponse
return SuccessResponse(
    data={"student_id": 123, "name": "John"},
    message="Operation successful"
)

# Exceptions auto-convert to ErrorResponse via handler
raise NotFoundException("Not found")
# → {"error": {"code": "NOT_FOUND", "message": "..."}, "status_code": 404}
```


# ============================================================================
# SECTION 3: Checklist for Migrating Each Route
# ============================================================================

For each route you migrate, check:

### Code Structure
- [ ] Remove direct `get_connection()` calls
- [ ] Remove direct cursor operations
- [ ] Use repository instead
- [ ] Use service instead of direct DeepFace/embedding calls

### Input Validation
- [ ] Add Pydantic schema for inputs
- [ ] Use schema in route signature
- [ ] Remove manual validation checks (Pydantic does it)
- [ ] Raise ValidationException for business logic validation

### Error Handling
- [ ] Replace try-except raw responses with custom exceptions
- [ ] Use NotFoundException for missing resources
- [ ] Use ValidationException for invalid input
- [ ] Use DatabaseException for DB errors
- [ ] Use ExternalServiceException for API failures

### Logging
- [ ] Replace all print() with logger calls
- [ ] Log at INFO level for important events
- [ ] Log at WARNING for potential issues
- [ ] Log at ERROR for failures with exc_info=True

### Response Format
- [ ] Use SuccessResponse for success cases
- [ ] Return Pydantic models (enable automatic docs)
- [ ] Include response_model in @router decorator
- [ ] Raise exceptions for error cases (not return error responses)

### Testing
- [ ] Can you pass mock repository to test?
- [ ] Does route have no direct DB dependencies?
- [ ] Are all parameters validated?
- [ ] Are error cases tested?


# ============================================================================
# SECTION 4: Migration Priority Order
# ============================================================================

Priority 1 (Critical):
- [ ] backend/api/face_routes.py - Most used, most complex
- [ ] backend/api/auth_routes.py - Security critical

Priority 2 (High):
- [ ] backend/api/student_routes.py
- [ ] backend/api/attendance_routes.py

Priority 3 (Medium):
- [ ] backend/api/stats_routes.py

Priority 4 (Optional):
- [ ] backend/services/attendance_service.py
- [ ] backend/services/auth_service.py
- [ ] backend/services/student_service.py


# ============================================================================
# SECTION 5: Command to Apply Migration
# ============================================================================

### Manual Migration (Recommended)
1. Create new file: `backend/api/face_routes_refactored.py` ✅ Done
2. Review differences
3. Test new implementation
4. Backup old file: `backend/api/face_routes_old.py`
5. Replace: `mv face_routes_refactored.py face_routes.py`
6. Run tests
7. Verify all endpoints in /api/docs

### File Structure After Migration
```
backend/
├── api/
│   ├── face_routes.py  (✅ Updated to new architecture)
│   ├── face_routes_old.py  (🔄 Backup of old implementation)
│   ├── auth_routes.py  (⬜ Next to update)
│   ├── student_routes.py  (⬜ To update)
│   └── attendance_routes.py  (⬜ To update)
├── db/
│   └── repositories.py  (✅ Created, used by routes)
├── services/
│   └── embedding_service.py  (✅ Created, used by routes)
└── core/
    ├── config.py  (✅ Created)
    ├── logger.py  (✅ Created)
    └── exceptions.py  (✅ Created)
```


# ============================================================================
# SECTION 6: Testing After Migration
# ============================================================================

### 1. Unit Tests (Test Repository/Service)
File: `backend/tests/test_repositories.py`
```python
def test_get_student_by_code():
    repo = StudentRepository()
    student = repo.get_student_by_code("SV001")
    assert student is not None
    assert student["code"] == "SV001"

def test_get_student_by_code_not_found():
    repo = StudentRepository()
    student = repo.get_student_by_code("INVALID")
    assert student is None
```

### 2. Integration Tests (Test Route + Repository)
File: `backend/tests/test_face_routes.py`
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_face_success():
    response = client.post(
        "/api/face/register",
        data={
            "student_code": "SV001",
            "full_name": "John Doe"
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["student_code"] == "SV001"

def test_register_face_not_found():
    response = client.post(
        "/api/face/register",
        data={
            "student_code": "INVALID",
            "full_name": "John"
        }
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

### 3. Manual Testing
```bash
# Test health check
curl http://localhost:8000/health

# Test new endpoint
curl -X POST http://localhost:8000/api/face/register \
  -H "Content-Type: multipart/form-data" \
  -F "student_code=SV001" \
  -F "full_name=John Doe"

# Check OpenAPI docs for schema
# http://localhost:8000/api/docs
```


# ============================================================================
# SECTION 7: Common Pitfalls & Solutions
# ============================================================================

### Pitfall 1: Forgetting to close connections
**Problem:** Connection leaks in old code
**Solution:** Use Repository pattern - it handles connection lifecycle

### Pitfall 2: Inconsistent response formats
**Problem:** Different routes return different error formats
**Solution:** Use SuccessResponse and raise exceptions consistently

### Pitfall 3: No validation at route level
**Problem:** Invalid data accepted and processed
**Solution:** Use Pydantic schemas with automatic validation

### Pitfall 4: Hard to test routes with embedded DB logic
**Problem:** Cannot test without database
**Solution:** Use dependency injection, pass mock repository to test

### Pitfall 5: Logging scattered and inconsistent
**Problem:** Cannot aggregate logs across system
**Solution:** Use structured JSON logging via get_logger()

### Pitfall 6: Direct embedding logic in routes
**Problem:** Same code repeated in multiple places
**Solution:** Use EmbeddingService, reuse across all routes


# ============================================================================
# SECTION 8: Files Available for Reference
# ============================================================================

### Completed Implementation:
- ✅ `backend/api/face_routes_refactored.py` - Full refactored example
- ✅ `backend/core/config.py` - Configuration setup
- ✅ `backend/core/logger.py` - Logging setup
- ✅ `backend/core/exceptions.py` - Exception hierarchy
- ✅ `backend/app/schemas.py` - Pydantic models
- ✅ `backend/db/repositories.py` - Repository pattern
- ✅ `backend/services/embedding_service.py` - Embedding logic

### Next Steps:
1. Review `face_routes_refactored.py`
2. Update `face_routes.py` (replace old with refactored)
3. Repeat process for other route files
4. Add tests in `backend/tests/`
5. Update frontend if needed

# ============================================================================
