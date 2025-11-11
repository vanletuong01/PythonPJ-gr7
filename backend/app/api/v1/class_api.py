from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.class_schemas import ClassCreate, ClassOut
from backend.app.crud.class_crud import create_class, get_all_majors, get_all_types, get_all_shifts
from backend.app.database import get_db

router = APIRouter()

@router.post("/create", response_model=ClassOut)
def api_create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    return create_class(db, class_in)

@router.get("/majors")
def api_get_majors(db: Session = Depends(get_db)):
    return get_all_majors(db)

@router.get("/types")
def api_get_types(db: Session = Depends(get_db)):
    return get_all_types(db)

@router.get("/shifts")
def api_get_shifts(db: Session = Depends(get_db)):
    return get_all_shifts(db)