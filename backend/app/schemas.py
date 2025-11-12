"""
Pydantic schemas for API request/response validation
Dùng cho FastAPI automatic validation, OpenAPI docs, error handling
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================
class ErrorCodeEnum(str, Enum):
    """Standard error codes for API responses"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# ============================================================================
# Response Schemas
# ============================================================================
class ErrorDetail(BaseModel):
    """Chi tiết lỗi trong response"""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: dict = Field(..., description="Error details")
    timestamp: str = Field(..., description="ISO format timestamp")
    request_id: Optional[str] = None
    path: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """Generic success response wrapper"""
    data: dict = Field(..., description="Response data")
    message: str = Field(default="Success", description="Success message")
    timestamp: str = Field(..., description="ISO format timestamp")


# ============================================================================
# Authentication Schemas
# ============================================================================
class RegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @validator("username")
    def username_alphanumeric(cls, v):
        assert v.isalnum(), "username must be alphanumeric"
        return v


class LoginRequest(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserResponse(BaseModel):
    """User profile response"""
    id: int
    username: str
    email: str
    full_name: str
    created_at: datetime


# ============================================================================
# Student Schemas
# ============================================================================
class StudentRequest(BaseModel):
    """Create/update student"""
    code: str = Field(..., min_length=1, max_length=50, description="Mã sinh viên")
    full_name: str = Field(..., min_length=2, max_length=100, description="Họ tên")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, regex=r"^\+?1?\d{9,15}$")
    class_name: Optional[str] = None
    
    @validator("code")
    def code_alphanumeric(cls, v):
        assert v.replace("-", "").replace("_", "").isalnum(), "code must be alphanumeric"
        return v


class StudentResponse(BaseModel):
    """Student profile response"""
    id: int
    code: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    class_name: Optional[str]
    photo_status: str = Field(..., description="pending|processing|completed")
    embedding_status: str = Field(..., description="pending|processing|completed")
    created_at: datetime
    updated_at: datetime


class StudentListResponse(BaseModel):
    """Paginated student list"""
    students: List[StudentResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ============================================================================
# Face Registration Schemas
# ============================================================================
class FaceRegisterRequest(BaseModel):
    """Start face registration session"""
    student_code: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @validator("student_code")
    def validate_code(cls, v):
        assert len(v.strip()) > 0, "student_code cannot be empty"
        return v


class FaceFrameUploadRequest(BaseModel):
    """Upload individual face frame during registration"""
    student_code: str = Field(..., min_length=1)
    index: int = Field(..., ge=0, le=50, description="Frame index 0-25")
    direction: str = Field(..., description="Đối mặt: front/left/right/up/down")


class FaceFinalizeRequest(BaseModel):
    """Finalize face registration after all frames uploaded"""
    student_code: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=2, max_length=100)


class FaceCheckRequest(BaseModel):
    """Check/recognize face for attendance"""
    image_url: Optional[str] = None
    quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    return_debug_info: bool = False


class FaceCheckResponse(BaseModel):
    """Face recognition response"""
    matched: bool
    student_code: Optional[str] = None
    full_name: Optional[str] = None
    confidence: Optional[float] = None
    distance: Optional[float] = None
    timestamp: datetime
    debug_info: Optional[dict] = None


class FaceEmbeddingResponse(BaseModel):
    """Face embedding response"""
    student_code: str
    full_name: str
    embedding_vector: Optional[List[float]] = None  # Don't expose raw embedding in production
    embedding_dimensions: int
    created_at: datetime


# ============================================================================
# Attendance Schemas
# ============================================================================
class AttendanceRecordRequest(BaseModel):
    """Manual attendance record"""
    student_code: str = Field(..., min_length=1)
    study_id: int = Field(..., gt=0)
    status: str = Field(..., regex="^(present|absent|late)$")
    notes: Optional[str] = None


class AttendanceRecordResponse(BaseModel):
    """Attendance record response"""
    id: int
    student_code: str
    student_name: str
    study_id: int
    status: str
    check_in_time: Optional[datetime]
    distance: Optional[float]
    embedding_used: bool
    created_at: datetime


class AttendanceListResponse(BaseModel):
    """Paginated attendance list"""
    records: List[AttendanceRecordResponse]
    total: int
    page: int
    limit: int
    study_date: Optional[str] = None


class DailyAttendanceSummary(BaseModel):
    """Daily attendance summary stats"""
    date: str
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    present_percentage: float


# ============================================================================
# Statistics Schemas
# ============================================================================
class StatisticsRequest(BaseModel):
    """Statistics query parameters"""
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
    student_code: Optional[str] = None
    class_name: Optional[str] = None
    group_by: str = Field(default="day", regex="^(day|week|month)$")


class StudentAttendanceStats(BaseModel):
    """Individual student attendance statistics"""
    student_code: str
    full_name: str
    total_sessions: int
    present: int
    absent: int
    late: int
    attendance_rate: float
    recognition_success_rate: float


class ClassAttendanceStats(BaseModel):
    """Class-level attendance statistics"""
    class_name: str
    total_students: int
    total_sessions: int
    avg_attendance_rate: float
    avg_recognition_success_rate: float
    by_student: List[StudentAttendanceStats]


# ============================================================================
# Health Check Schemas
# ============================================================================
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., regex="^(healthy|unhealthy|degraded)$")
    timestamp: datetime
    version: str
    checks: Optional[dict] = None


class ReadinessProbeResponse(BaseModel):
    """Readiness probe response"""
    status: str = Field(..., regex="^(ready|not_ready)$")
    timestamp: datetime
    reason: Optional[str] = None


# ============================================================================
# Pagination Schemas
# ============================================================================
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


# ============================================================================
# Batch Operation Schemas
# ============================================================================
class BatchUploadRequest(BaseModel):
    """Batch upload face images"""
    student_code: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=2)
    image_count: int = Field(..., ge=1, le=50)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    total_uploaded: int
    successful: int
    failed: int
    failed_indices: List[int]
    embedding_computed: bool
    message: str
