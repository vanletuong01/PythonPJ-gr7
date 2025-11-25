from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# ===== THÊM LOG DEBUG =====
print("="*60)
print("🔍 [DATABASE CONFIG DEBUG]")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
print("="*60)
# ==========================

# Lấy thông tin từ .env
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "python_project")

# Tạo connection string với SSL cho Aiven
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Thêm SSL nếu không phải localhost
if DB_HOST not in ["localhost", "127.0.0.1"]:
    DATABASE_URL += "?ssl_mode=REQUIRED"

print(f"🔗 DATABASE_URL: {DATABASE_URL.replace(DB_PASSWORD, '***')}")
print("="*60)

# Tạo engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()