from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date

class ClassCreate(BaseModel):
    quantity: int
    semester: str
    date_start: date
    date_end: date
    class_name: str
    full_class_name: str | None = None
    course_code: int | None = None
    teacher_class: str
    session: str
    TypeID: int
    MajorID: int
    ShiftID: int
    id_login: int

    @field_validator('teacher_class', 'session', 'class_name')
    @classmethod
    def check_not_empty(cls, v, info):
        if not v or v.strip() == "":
            raise ValueError(f"{info.field_name} không được để trống")
        return v.strip()

    @field_validator('quantity')
    @classmethod
    def check_positive(cls, v):
        if v < 1:
            raise ValueError("Sĩ số phải > 0")
        return v

    @field_validator('course_code')
    @classmethod
    def check_course_code(cls, v):
        if v is not None and v < 0:
            raise ValueError("course_code phải >= 0")
        return v

    @field_validator('date_end')
    @classmethod
    def check_date_range(cls, v, info):
        if 'date_start' in info.data and v < info.data['date_start']:
            raise ValueError("Ngày kết thúc phải sau ngày bắt đầu")
        return v

class ClassOut(BaseModel):
    ClassID: int
    ClassName: str
    FullClassName: str | None = None
    Teacher_class: str | None = None
    Quantity: int
    Semester: str
    DateStart: date
    DateEnd: date
    Session: str | None = None
    CourseCode: int | None = None
    ShiftID: int | None = None   # <-- Thêm dòng này
    model_config = ConfigDict(from_attributes=True)

class ManualAttendanceRequest(BaseModel):
    study_id: int
    session_date: str