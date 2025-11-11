from sqlalchemy.orm import Session
from backend.app.models.user import Teacher
from backend.app.schemas.user import TeacherCreate
from backend.app.services.auth_service import hash_password

def get_teacher_by_username(db: Session, username: str):
    return db.query(Teacher).filter(Teacher.username == username).first()

def create_teacher(db: Session, teacher: TeacherCreate):
    db_teacher = Teacher(
        username=teacher.username,
        hashed_password=hash_password(teacher.password),
        full_name=teacher.full_name
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher