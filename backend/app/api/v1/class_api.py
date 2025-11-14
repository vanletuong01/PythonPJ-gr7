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

router = APIRouter()

@router.post("/create", response_model=ClassOut)
def api_create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    try:
        result = create_class(db, class_data)
        print(f"[api_create_class] SUCCESS ClassID={result.ClassID}")
        return result
    except ValueError as e:
        # Lỗi validation (mã lớp trùng)
        print(f"[api_create_class] ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        print(f"[api_create_class] IntegrityError: {e.orig}")
        raise HTTPException(status_code=400, detail=f"Lỗi ràng buộc DB: {e.orig}")
    except Exception as e:
        print(f"[api_create_class] ERROR: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=list[ClassOut])
def api_list_classes(db: Session = Depends(get_db)):
    return get_all_classes(db)

@router.get("/dashboard/stats")
def api_dashboard_stats(db: Session = Depends(get_db)):
    """Thống kê cho dashboard"""
    total_classes = db.query(func.count(Class.ClassID)).scalar()
    total_students = db.query(func.sum(Class.Quantity)).scalar() or 0
    
    # Sĩ số theo tháng (giả sử lấy theo DateStart)
    attendance_by_month = db.query(
        func.date_format(Class.DateStart, '%Y-%m').label('month'),
        func.count(Class.ClassID).label('count')
    ).group_by('month').order_by('month').limit(6).all()
    
    return {
        "total_classes": total_classes,
        "total_students": total_students,
        "attendance_by_month": [{"month": m, "count": c} for m, c in attendance_by_month]
    }

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