from sqlalchemy.orm import Session
from backend.app.crud.major_crud import get_all_majors

def get_majors_service(db: Session):
    return get_all_majors(db)
