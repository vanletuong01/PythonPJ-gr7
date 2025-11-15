from fastapi import APIRouter, Depends
from backend.app.schemas.student_schemas import StudentCreate
from backend.app.services.student_service import create_student
from backend.app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/student/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, data)
