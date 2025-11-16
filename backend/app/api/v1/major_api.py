from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# ĐÚNG: get_db nằm ở backend/app/database.py
from backend.app.database import get_db  

from backend.app.schemas.major_schemas import MajorResponse
from backend.app.services.major_service import get_majors_service

router = APIRouter()

@router.get("/", response_model=list[MajorResponse])
def get_majors(db: Session = Depends(get_db)):
    return get_majors_service(db)
