from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.models.class_model import Class
from backend.app.schemas.class_schemas import ClassCreate

def create_class(db: Session, class_in: ClassCreate):
    db_class = Class(
        Quantity=class_in.quantity,
        Rank=class_in.rank,
        Semester=class_in.semester,
        DateStart=class_in.date_start,
        DateEnd=class_in.date_end,
        Session=class_in.session,
        ClassName=class_in.class_name,
        FullClassName=class_in.full_class_name,
        Teacher_class=class_in.teacher_class,
        TypeID=class_in.type_id,
        MajorID=class_in.major_id,
        ShiftID=class_in.shift_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class
def get_all_majors(db: Session):
    rows = db.execute(text("SELECT MajorID, MajorName FROM major")).fetchall()
    return [{"MajorID": row[0], "MajorName": row[1]} for row in rows]

def get_all_types(db: Session):
    rows = db.execute(text("SELECT TypeID, TypeName FROM type")).fetchall()
    return [{"TypeID": row[0], "TypeName": row[1]} for row in rows]

def get_all_shifts(db: Session):
    rows = db.execute(text("SELECT ShiftID, ShiftName FROM shift")).fetchall()
    return [{"ShiftID": row[0], "ShiftName": row[1]} for row in rows]