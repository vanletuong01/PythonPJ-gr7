from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.database import get_db
from backend.app.services.student_service import search_students, create_student
from backend.app.schemas.student_schemas import StudentCreate

router = APIRouter(tags=["Student"])

@router.get("/search")
def search_students(q: str = Query(..., min_length=1), limit: int = 30, db: Session = Depends(get_db)):
    # Tìm theo tên hoặc mã số sinh viên (StudentCode)
    results = (
        db.query(Student)
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
            "Full_name_mj": getattr(s, "Full_name_mj", None),
            "TypeName": getattr(s, "TypeName", None),
            "ClassID": getattr(s, "ClassID", None)
        }
        for s in results
    ]

@router.post("/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, data)
