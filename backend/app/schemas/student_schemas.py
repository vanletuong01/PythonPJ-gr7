from pydantic import BaseModel
from datetime import date

class StudentCreate(BaseModel):
    FullName: str
    StudentCode: str
    DefaultClass: str
    Phone: str | None = None
    AcademicYear: str
    DateOfBirth: date
    CitizenID: str
    MajorID: int
    TypeID: int
    PhotoStatus: str = "NONE"
    StudentPhoto: str | None = None
