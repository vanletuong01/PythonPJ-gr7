import time
from sqlalchemy.orm import Session
from backend.app.models.login import Login
from backend.app.schemas.login_schemas import LoginCreate, LoginIn
from backend.app.services.auth_service import hash_password, verify_password

def get_login_by_email(db: Session, email: str):
    return db.query(Login).filter(Login.email == email).first()

def create_login(db: Session, login: LoginCreate):
    print(f"[create_login] START email={login.email}")
    t0 = time.time()
    
    # Kiểm tra email trùng
    existing = db.query(Login).filter(Login.email == login.email).first()
    if existing:
        raise ValueError(f"Email {login.email} đã tồn tại")
    
    hashed = hash_password(login.password)
    print(f"[create_login] Hash done {int((time.time()-t0)*1000)}ms")
    
    db_login = Login(
        email=login.email,
        phone=login.phone,
        name=login.name,
        pass_field=hashed
    )
    db.add(db_login)
    print(f"[create_login] Added to session")
    
    try:
        db.commit()
        print(f"[create_login] Commit OK {int((time.time()-t0)*1000)}ms")
    except Exception as e:
        db.rollback()
        print(f"[create_login] Commit ERROR: {e!r}")
        raise
    
    db.refresh(db_login)
    print(f"[create_login] DONE id={db_login.id_login} total={int((time.time()-t0)*1000)}ms")
    return db_login

def login_user(db: Session, login: LoginIn):
    user = db.query(Login).filter(Login.email == login.email).first()
    if not user or not verify_password(login.password, user.pass_field or ""):
        return {"success": False, "message": "Email hoặc mật khẩu không đúng"}
    return {
        "success": True,
        "id_login": user.id_login,
        "email": user.email,
        "name": user.name,
        "phone": user.phone
    }