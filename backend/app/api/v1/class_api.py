from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.class_crud import create_class as crud_create_class, get_all_majors, get_all_types, get_all_shifts

router = APIRouter()

@router.post("/create")
async def api_create_class(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        # debug log
        print("DEBUG payload:", payload)
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