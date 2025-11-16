from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.student import Student
from backend.app.models.study import Study

def search_students(db: Session, q: str, limit: int = 30):
    if not q or len(q.strip()) < 2:
        return {"success": True, "data": []}

    like = f"%{q}%"

    rows = (
        db.query(Student, Study.ClassID)
        .join(Study, Study.StudentID == Student.StudentID, isouter=True)
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
