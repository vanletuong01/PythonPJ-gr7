from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.student import Student
from backend.app.models.study import Study

def search_students(db: Session, q: str, limit: int = 30):
    q = (q or "").strip()
    if len(q) < 2:
        return {"success": True, "data": []}

    like = f"%{q}%"

    rows = (
        db.query(Student, Study.ClassID)
        .outerjoin(Study, Study.StudentID == Student.StudentID)
        .filter(
            or_(
                Student.FullName.ilike(like),
                Student.StudentCode.ilike(like)
            )
        )
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "data": [
            {
                "StudentCode": r.Student.StudentCode,
                "FullName": r.Student.FullName,
                "ClassID": r.ClassID,      # <-- ClassID từ Study
                "Phone": r.Student.Phone
            }
            for r in rows
        ]
    }

def create_student(db: Session, data):
    student = Student(
        FullName=data.FullName,
        StudentCode=data.StudentCode,
        DefaultClass=data.DefaultClass,
        Phone=data.Phone,
        AcademicYear=data.AcademicYear,
        DateOfBirth=data.DateOfBirth,
        CitizenID=data.CitizenID,
        MajorID=data.MajorID,
        TypeID=data.TypeID,
        PhotoStatus=getattr(data, "PhotoStatus", "NONE"),
        StudentPhoto=getattr(data, "StudentPhoto", None)
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"success": True, "student_id": student.StudentID}
