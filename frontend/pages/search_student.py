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

    result = []

    for stu, class_id in rows:
        result.append({
            "StudentCode": stu.StudentCode,
            "FullName": stu.FullName,
            "ClassID": class_id,
            "Phone": stu.Phone
        })

    return {"success": True, "data": result}
