from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.models.major import Major
from backend.app.models.type import Type

def get_student_detail(db: Session, student_id: int):
    result = (
        db.query(
            Student,
            Major.Full_name_mj,
            Type.TypeName
        )
        .join(Major, Student.MajorID == Major.MajorID)
        .join(Type, Student.TypeID == Type.TypeID)
        .filter(Student.StudentID == student_id)
        .first()
    )
    if not result:
        return None
    s, full_name_mj, type_name = result
    return {
        "StudentID": s.StudentID,
        "FullName": s.FullName,
        "StudentCode": s.StudentCode,
        "DefaultClass": getattr(s, "DefaultClass", ""),
        "Phone": getattr(s, "Phone", ""),
        "AcademicYear": getattr(s, "AcademicYear", ""),
        "DateOfBirth": s.DateOfBirth.strftime("%d/%m/%Y") if hasattr(s.DateOfBirth, "strftime") else (s.DateOfBirth or ""),
        "CitizenID": getattr(s, "CitizenID", ""),
        "PhotoStatus": getattr(s, "PhotoStatus", ""),
        "StudentPhoto": getattr(s, "StudentPhoto", ""),
        "Full_name_mj": full_name_mj,
        "TypeName": type_name
    }