from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time

# ==================== Login/Auth Models ====================

class LoginRequest(BaseModel):
    """Model cho request đăng nhập giảng viên"""
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., alias="pass")

class LoginResponse(BaseModel):
    """Model cho response đăng nhập"""
    success: bool
    message: str
    teacher: Optional[dict] = None
    token: Optional[str] = None

# ==================== Student Models ====================

class StudentRegisterRequest(BaseModel):
    """Model cho request đăng ký sinh viên"""
    student_code: str
    full_name: str
    default_class: Optional[str] = None
    phone: Optional[str] = None
    academic_year: Optional[str] = None
    date_of_birth: Optional[date] = None
    citizen_id: Optional[str] = None
    major_id: int
    type_id: int

class StudentResponse(BaseModel):
    """Model cho response sinh viên"""
    success: bool
    message: str
    student: Optional[dict] = None

class Student(BaseModel):
    """Model sinh viên (alias của StudentInfo)"""
    StudentID: Optional[int] = None
    FullName: str
    StudentCode: str
    DefaultClass: Optional[str] = None
    Phone: Optional[str] = None
    AcademicYear: Optional[str] = None
    DateOfBirth: Optional[date] = None
    CitizenID: Optional[str] = None
    PhotoStatus: Optional[str] = None
    StudentPhoto: Optional[str] = None
    MajorID: int
    TypeID: int

class StudentInfo(BaseModel):
    """Model thông tin sinh viên từ database"""
    StudentID: Optional[int] = None
    FullName: str
    StudentCode: str
    DefaultClass: Optional[str] = None
    Phone: Optional[str] = None
    AcademicYear: Optional[str] = None
    DateOfBirth: Optional[date] = None
    CitizenID: Optional[str] = None
    PhotoStatus: Optional[str] = None
    StudentPhoto: Optional[str] = None
    MajorID: int
    TypeID: int

# ==================== Class Models ====================

class ClassInfo(BaseModel):
    """Model thông tin lớp học"""
    ClassID: Optional[int] = None
    ClassName: str
    FullClassName: Optional[str] = None
    Quantity: int
    Semester: str
    DateStart: date
    DateEnd: date
    Session: Optional[str] = None
    Teacher_class: Optional[str] = None
    TypeID: int
    MajorID: int
    ShiftID: int

# ==================== Attendance Models ====================

class Attendance(BaseModel):
    """Model điểm danh (alias của AttendanceRecord)"""
    AttendanceID: Optional[int] = None
    StudyID: int
    Date: date
    Time: time
    PhotoPath: Optional[str] = None

class AttendanceRecord(BaseModel):
    """Model bản ghi điểm danh"""
    AttendanceID: Optional[int] = None
    StudyID: int
    Date: date
    Time: time
    PhotoPath: Optional[str] = None

class AttendanceCheckRequest(BaseModel):
    """Request điểm danh cho lớp"""
    class_id: int = Field(..., description="ID lớp học")
    date: Optional[str] = Field(None, description="Ngày điểm danh (YYYY-MM-DD)")

class AttendanceResponse(BaseModel):
    """Response cho attendance"""
    success: bool
    message: str
    data: Optional[dict] = None

class AttendanceCheckResponse(BaseModel):
    """Response kết quả điểm danh"""
    success: bool
    message: str
    student: Optional[dict] = None
    attendance_time: Optional[str] = None
    confidence: Optional[float] = None

# ==================== Embedding Models ====================

class FaceEmbedding(BaseModel):
    """Model face embedding (alias của StudentEmbedding)"""
    EmbeddingID: Optional[int] = None
    StudentID: int
    Embedding: bytes
    EmbeddingDim: int
    PhotoPath: Optional[str] = None
    Quality: Optional[float] = None
    Source: Optional[str] = None
    CreatedAt: Optional[datetime] = None

class StudentEmbedding(BaseModel):
    """Model face embedding của sinh viên"""
    EmbeddingID: Optional[int] = None
    StudentID: int
    Embedding: bytes
    EmbeddingDim: int
    PhotoPath: Optional[str] = None
    Quality: Optional[float] = None
    Source: Optional[str] = None
    CreatedAt: Optional[datetime] = None

# ==================== Response Models ====================

class StudentListResponse(BaseModel):
    """Response danh sách sinh viên trong lớp"""
    total: int
    students: list

class AttendanceListResponse(BaseModel):
    """Response danh sách điểm danh"""
    date: str
    class_id: int
    class_name: str
    total_students: int
    attended: int
    absent: int
    attendance_list: list

class StatsResponse(BaseModel):
    """Response thống kê"""
    total_students: int
    attendance_today: int
    attendance_rate: float
    date: str
