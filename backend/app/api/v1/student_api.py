from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.models.major import Major
from backend.app.models.type import Type
from backend.app.database import get_db
from backend.app.services.student_service import search_students, create_student
from backend.app.schemas.student_schemas import StudentCreate

router = APIRouter(tags=["Student"])

@router.get("/search")
def search_students(q: str = Query(..., min_length=1), limit: int = 30, db: Session = Depends(get_db)):
    # Tìm theo tên hoặc mã số sinh viên (StudentCode)
    results = (
        db.query(
            Student,
            Major.Full_name_mj,
            Type.TypeName
        )
        .join(Major, Student.MajorID == Major.MajorID)
        .join(Type, Student.TypeID == Type.TypeID)
        .filter(
            (Student.FullName.ilike(f"%{q}%")) |
            (Student.StudentCode.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    # Trả về dữ liệu dạng list[dict]
    return [
        {
            "StudentID": s.StudentID,
            "FullName": s.FullName,
            "StudentCode": s.StudentCode,
            "DefaultClass": getattr(s, "DefaultClass", None),
            "Phone": getattr(s, "Phone", None),
            "DateOfBirth": getattr(s, "DateOfBirth", None),
            "CitizenID": getattr(s, "CitizenID", None),
            "AcademicYear": getattr(s, "AcademicYear", None),
            "Full_name_mj": full_name_mj,
            "TypeName": type_name,
            "ClassID": getattr(s, "ClassID", None),
            "MajorID": getattr(s, "MajorID", None),
            "TypeID": getattr(s, "TypeID", None),
            "PhotoStatus": getattr(s, "PhotoStatus", None)
        }
        for s, full_name_mj, type_name in results
    ]

@router.post("/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, data)
