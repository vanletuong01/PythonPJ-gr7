from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.student_service import search_students, create_student
from backend.app.schemas.student_schemas import StudentCreate

router = APIRouter(tags=["Student"])

@router.get("/search")
def search_student_api(
    q: str = Query(..., min_length=2),
    limit: int = 30,
    db: Session = Depends(get_db)
):
    return search_students(db, q=q, limit=limit)

@router.post("/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, data)
