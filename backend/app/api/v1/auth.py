from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.login import LoginCreate, LoginIn, LoginOut
from backend.app.crud.login import create_login, login_user

router = APIRouter()

@router.post("/register", response_model=LoginOut, response_model_exclude_none=True)
def register(login: LoginCreate, db: Session = Depends(get_db)):
    try:
        return create_login(db, login)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(login: LoginIn, db: Session = Depends(get_db)):
    result = login_user(db, login)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("message"))
    return result