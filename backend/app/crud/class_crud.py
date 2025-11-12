from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.models.class_model import Class
from backend.app.schemas.class_schemas import ClassCreate
import datetime
def get_weekday(date_str):
    # date_str: 'YYYY-MM-DD'
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        weekday_map = {
            0: "Thứ 2",
            1: "Thứ 3",
            2: "Thứ 4",
            3: "Thứ 5",
            4: "Thứ 6",
            5: "Thứ 7",
            6: "Chủ nhật"
        }
        return weekday_map[date_obj.weekday()]
    except Exception:
        return None
    
def create_class(db: Session, payload):
    # payload: dict từ frontend
    classname = payload.get("class_name") or payload.get("ClassName") or ""
    full = payload.get("full_class_name") or payload.get("FullClassName") or ""
    quantity = payload.get("quantity") or 0
    new = Class(
        Quantity=int(quantity),
        Semester=payload.get("semester",""),
        DateStart=payload.get("date_start"),
        DateEnd=payload.get("date_end"),
        Session=payload.get("session"),
        ClassName=classname,
        FullClassName=full,
        Teacher_class=payload.get("teacher_class"),
        TypeID=payload.get("type_id"),
        MajorID=payload.get("major_id"),
        ShiftID=payload.get("shift_id")
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
def get_all_majors(db: Session):
    rows = db.execute(text("SELECT MajorID, MajorName FROM major")).fetchall()
    return [{"MajorID": row[0], "MajorName": row[1]} for row in rows]

def get_all_types(db: Session):
    rows = db.execute(text("SELECT TypeID, TypeName FROM type")).fetchall()
    return [{"TypeID": row[0], "TypeName": row[1]} for row in rows]

def get_all_shifts(db: Session):
    rows = db.execute(text("SELECT ShiftID, ShiftName FROM shift")).fetchall()
    return [{"ShiftID": row[0], "ShiftName": row[1]} for row in rows]