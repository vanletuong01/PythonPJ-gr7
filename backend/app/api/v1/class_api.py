from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.schemas.class_schemas import ClassCreate, ClassOut
from backend.app.crud.class_crud import create_class, get_all_classes
from backend.app.models.major import Major
from backend.app.models.type import Type
from backend.app.models.shift import Shift
from backend.app.models.class_model import Class
from backend.app.models.teach import Teach
from backend.app.models.study import Study
from backend.app.models.student import Student
from backend.app.models.attendance import Attendance
from pydantic import BaseModel

router = APIRouter()

# ------------------ GET ALL CLASSES ------------------
@router.get("/", response_model=list[ClassOut])
def api_get_all_classes(db: Session = Depends(get_db)):
    return get_all_classes(db)

# ------------------ CREATE CLASS ------------------
@router.post("/create", response_model=ClassOut)
def api_create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    try:
        result = create_class(db, class_data)

        id_login = getattr(class_data, "id_login", None)
        if id_login:
            new_teach = Teach(id_login=id_login, ClassID=result.ClassID)
            db.add(new_teach)
            db.commit()

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Lỗi ràng buộc DB: {e.orig}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------ LIST CLASSES ------------------
@router.get("/list", response_model=list[ClassOut])
def api_list_classes(db: Session = Depends(get_db)):
    return get_all_classes(db)

# ------------------ STATS ------------------
@router.get("/dashboard/stats")
def api_dashboard_stats(db: Session = Depends(get_db)):
    total_classes = db.query(func.count(Class.ClassID)).scalar()
    total_students = db.query(func.sum(Class.Quantity)).scalar() or 0

    attendance_by_month = db.query(
        func.date_format(Class.DateStart, '%Y-%m').label('month'),
        func.count(Class.ClassID).label('count')
    ).group_by('month').order_by('month').limit(6).all()

    return {
        "total_classes": total_classes,
        "total_students": total_students,
        "attendance_by_month": [{"month": m, "count": c} for m, c in attendance_by_month]
    }

# ------------------ DROPDOWN DATA ------------------
@router.get("/majors")
def api_get_majors(db: Session = Depends(get_db)):
    majors = db.query(Major).all()
    return [{"MajorID": m.MajorID, "MajorName": m.MajorName} for m in majors]

@router.get("/types")
def api_get_types(db: Session = Depends(get_db)):
    types = db.query(Type).all()
    return [{"TypeID": t.TypeID, "TypeName": t.TypeName} for t in types]

@router.get("/shifts")
def api_get_shifts(db: Session = Depends(get_db)):
    shifts = db.query(Shift).all()
    return [{"ShiftID": s.ShiftID, "ShiftName": s.ShiftName} for s in shifts]

# ------------------ CLASSES OF TEACHER ------------------
@router.get("/by_teacher/{id_login}")
def get_classes_by_teacher(id_login: int, db: Session = Depends(get_db)):
    classes = (
        db.query(Class)
        .join(Teach, Class.ClassID == Teach.ClassID)
        .filter(Teach.id_login == id_login)
        .all()
    )
    return [c.__dict__ for c in classes]

# ------------------ STUDENTS IN CLASS ------------------
@router.get("/students_in_class/{class_id}")
def get_students_in_class(class_id: int, db: Session = Depends(get_db)):
    # Code y hệt cũ
    results = (
        db.query(Student.StudentID, Student.FullName, Student.StudentCode)
        .join(Study, Study.StudentID == Student.StudentID)
        .filter(Study.ClassID == class_id)
        .all()
    )
    return [
        {
            "StudentID": s.StudentID,
            "FullName": s.FullName,
            "StudentCode": s.StudentCode
        }
        for s in results
    ]
# ------------------ ATTENDANCE REPORT ------------------
@router.get("/attendance_by_date/{class_id}")
def attendance_by_date(class_id: int, db: Session = Depends(get_db)):
    result = (
        db.query(Attendance.Date, func.count(Study.StudentID).label("present"))
        .join(Study, Attendance.StudyID == Study.StudyID)
        .filter(Study.ClassID == class_id)
        .group_by(Attendance.Date)
        .order_by(Attendance.Date)
        .all()
    )
    return [{"date": r[0], "present": r[1]} for r in result]


# ============================================================
#     ⭐⭐⭐ API GÁN SINH VIÊN VÀO LỚP (QUAN TRỌNG NHẤT) ⭐⭐⭐
# ============================================================

class AssignStudentRequest(BaseModel):
    student_id: int
    class_id: int

@router.post("/assign")
def assign_student_to_class(payload: AssignStudentRequest, db: Session = Depends(get_db)):
    # Kiểm tra class
    cls = db.query(Class).filter(Class.ClassID == payload.class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    # Kiểm tra student
    student = db.query(Student).filter(Student.StudentID == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Kiểm tra trùng
    exists = db.query(Study).filter(
        Study.ClassID == payload.class_id,
        Study.StudentID == payload.student_id
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="Student already in this class")

    # Thêm vào bảng Study
    new_study = Study(
        ClassID=payload.class_id,
        StudentID=payload.student_id
    )
    db.add(new_study)

    # tăng sĩ số lớp
    cls.Quantity = (cls.Quantity or 0) + 1

    db.commit()

    return {"message": "Student assigned successfully", "class_id": payload.class_id}
