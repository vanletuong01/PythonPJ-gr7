import time
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from backend.config import SECRET_KEY, ALGORITHM

# Dùng pbkdf2_sha256 cho thực tế, an toàn và tương thích với hash hiện tại
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    print("HASH PASSWORD INPUT:", repr(password), type(password), len(password) if password else "None")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
