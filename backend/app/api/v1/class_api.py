from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.class_crud import create_class as crud_create_class, get_all_majors, get_all_types, get_all_shifts

# Thêm import các model
from backend.app.models.type import Type
from backend.app.models.major import Major
from backend.app.models.shift import Shift

router = APIRouter()

@router.post("/create")
async def api_create_class(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        print("DEBUG payload:", payload)

        # Tra ID từ tên
        type_obj = db.query(Type).filter(Type.TypeName == payload.get("type")).first()
        major_obj = db.query(Major).filter(Major.MajorName == payload.get("major")).first()
        shift_obj = db.query(Shift).filter(Shift.ShiftName == payload.get("shift")).first()

        # Gán ID vào payload, nếu không tìm thấy thì trả lỗi
        payload["TypeID"] = type_obj.TypeID if type_obj else None
        payload["MajorID"] = major_obj.MajorID if major_obj else None
        payload["ShiftID"] = shift_obj.ShiftID if shift_obj else None

        # Xoá các trường tên nếu không cần
        payload.pop("type", None)
        payload.pop("major", None)
        payload.pop("shift", None)

        # Kiểm tra nếu thiếu ID thì trả lỗi
        if not payload["TypeID"] or not payload["MajorID"] or not payload["ShiftID"]:
            raise HTTPException(status_code=400, detail="Type, Major hoặc Shift không hợp lệ!")

        created = crud_create_class(db, payload)
        return {"status": "ok", "id": created.ClassID}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/majors")
def api_get_majors(db: Session = Depends(get_db)):
    return get_all_majors(db)

@router.get("/types")
def api_get_types(db: Session = Depends(get_db)):
    return get_all_types(db)

@router.get("/shifts")
def api_get_shifts(db: Session = Depends(get_db)):
    return get_all_shifts(db)