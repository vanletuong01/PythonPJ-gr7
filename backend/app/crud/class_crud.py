from sqlalchemy.orm import Session
from backend.app.models.teach import Teach
from backend.app.models.class_model import Class
from backend.app.schemas.class_schemas import ClassCreate
import sqlalchemy
from sqlalchemy import text

def create_class(db: Session, class_data: ClassCreate):
    print(f"[create_class] START data={class_data.model_dump()}")
    
    # Kiểm tra mã lớp đã tồn tại
    existing = db.query(Class).filter(Class.ClassName == class_data.class_name).first()
    if existing:
        print(f"[create_class] ClassName '{class_data.class_name}' đã tồn tại (ClassID={existing.ClassID})")
        raise ValueError(f"Mã lớp '{class_data.class_name}' đã tồn tại trong hệ thống")
    
    db_class = Class(
        Quantity=class_data.quantity,
        Semester=class_data.semester,
        DateStart=class_data.date_start,
        DateEnd=class_data.date_end,
        ClassName=class_data.class_name,
        FullClassName=class_data.full_class_name,
        CourseCode=class_data.course_code,
        Teacher_class=class_data.teacher_class,
        Session=class_data.session,
        #Rank=class_data.rank,
        TypeID=class_data.TypeID,
        MajorID=class_data.MajorID,
        ShiftID=class_data.ShiftID
    )
    
    db.add(db_class)
    try:
        db.commit()
        db.refresh(db_class)
        print(f"[create_class] COMMIT OK ClassID={db_class.ClassID}")
        
        if hasattr(class_data, "id_login") and class_data.id_login:
            db_teach = Teach(id_login=class_data.id_login, ClassID=db_class.ClassID)
            db.add(db_teach)
            db.commit()
            print(f"[create_class] Added to teach: id_login={class_data.id_login}, ClassID={db_class.ClassID}")

        return db_class
    except Exception as e:
        db.rollback()
        print(f"[create_class] ROLLBACK error={e!r}")
        raise e

def get_all_classes(db: Session):
    return db.query(Class).all()

def get_all_majors(db: Session):
    rows = db.execute(text("SELECT MajorID, MajorName FROM major")).fetchall()
    return [{"MajorID": row[0], "MajorName": row[1]} for row in rows]

def get_all_types(db: Session):
    rows = db.execute(text("SELECT TypeID, TypeName FROM type")).fetchall()
    return [{"TypeID": row[0], "TypeName": row[1]} for row in rows]

def get_all_shifts(db: Session):
    rows = db.execute(text("SELECT ShiftID, ShiftName FROM shift")).fetchall()
    return [{"ShiftID": row[0], "ShiftName": row[1]} for row in rows]