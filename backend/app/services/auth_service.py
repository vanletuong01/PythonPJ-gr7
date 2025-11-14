import time
from passlib.hash import pbkdf2_sha256
from jose import jwt
from datetime import datetime, timedelta
from backend.config import SECRET_KEY, ALGORITHM

def hash_password(password: str) -> str:
    t0 = time.time()
    print(f"[hash_password] START len={len(password)}")
    h = pbkdf2_sha256.hash(password)
    print(f"[hash_password] DONE len_hash={len(h)} time={int((time.time()-t0)*1000)}ms")
    return h

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)