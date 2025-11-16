from sqlalchemy.orm import Session
from backend.app.models.type import Type

def get_all_types(db: Session):
    return db.query(Type).all()
