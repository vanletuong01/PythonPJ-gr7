from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.user import TeacherCreate, TeacherLogin, TeacherOut
from backend.app.crud.user import get_teacher_by_username, create_teacher
from backend.app.services.auth_service import verify_password, create_access_token
from backend.app.database import get_db

router = APIRouter()

@router.post("/register", response_model=TeacherOut)
def register(teacher: TeacherCreate, db: Session = Depends(get_db)):
    if get_teacher_by_username(db, teacher.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_teacher(db, teacher)

@router.post("/login")
def login(teacher: TeacherLogin, db: Session = Depends(get_db)):
    db_teacher = get_teacher_by_username(db, teacher.username)
    if not db_teacher or not verify_password(teacher.password, db_teacher.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_teacher.username})
    return {"access_token": token, "token_type": "bearer"}