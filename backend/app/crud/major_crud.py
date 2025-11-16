from sqlalchemy.orm import Session
from backend.app.models.major import Major

def get_all_majors(db: Session):
    return db.query(Major).all()
