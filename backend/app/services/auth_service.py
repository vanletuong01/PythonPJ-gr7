import hashlib
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from backend.config import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password với bcrypt, tự động xử lý giới hạn 72 bytes"""
    if not password or not isinstance(password, str):
        raise ValueError("Password phải là chuỗi không rỗng")
    
    # Nếu password dài, hash trước bằng SHA256 để giảm độ dài
    if len(password.encode('utf-8')) > 72:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password với xử lý tương tự hash_password"""
    if not plain_password or not isinstance(plain_password, str):
        return False
    
    # Áp dụng cùng logic với hash_password
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)