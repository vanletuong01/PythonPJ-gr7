from sqlalchemy.orm import Session
from backend.app.models.login import Login
from backend.app.schemas.login import LoginCreate
from backend.app.services.auth_service import hash_password

def get_login_by_email(db: Session, email: str):
    return db.query(Login).filter(Login.email == email).first()

def create_login(db: Session, login: LoginCreate):
    db_login = Login(
        email=login.email,
        phone=login.phone,
        name=login.name,
        pass_field=hash_password(login.password)
    )
    db.add(db_login)
    db.commit()
    db.refresh(db_login)
    return db_login