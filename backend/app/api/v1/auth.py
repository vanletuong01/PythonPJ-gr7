from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.login import LoginCreate, LoginIn, LoginOut
from backend.app.crud.login import get_login_by_email, create_login
from backend.app.services.auth_service import verify_password, create_access_token
from backend.app.database import get_db

router = APIRouter()

@router.post("/register", response_model=LoginOut)
def register(login: LoginCreate, db: Session = Depends(get_db)):
    if get_login_by_email(db, login.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_login(db, login)

@router.post("/login")
def login(login: LoginIn, db: Session = Depends(get_db)):
    db_login = get_login_by_email(db, login.email)
    if not db_login or not verify_password(login.password, db_login.pass_field):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_login.email})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id_login": db_login.id_login,
        "email": db_login.email,
        "name": db_login.name,
        "phone": db_login.phone
    }}