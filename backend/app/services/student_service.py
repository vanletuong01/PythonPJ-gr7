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

    data = []
    for s, class_id in rows:
        data.append({
            "StudentCode": s.StudentCode,
            "FullName": s.FullName,
            "ClassID": class_id or "",
            "Phone": s.Phone or ""
        })

    return {"success": True, "data": data}
