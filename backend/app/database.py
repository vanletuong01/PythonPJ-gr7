from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy thông tin từ environment variables
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "python_project")

# Tạo connection string (KHÔNG CÓ ssl_mode)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("="*60)
print("[DATABASE CONFIG]")
print(f"DB_HOST: {DB_HOST}")
print(f"DB_PORT: {DB_PORT}")
print(f"DB_USER: {DB_USER}")
print(f"DB_NAME: {DB_NAME}")
print(f"DATABASE_URL: {DATABASE_URL.replace(DB_PASSWORD, '***')}")
print("="*60)

# Cấu hình SSL cho Aiven (nếu không phải localhost)
connect_args = {}
if DB_HOST not in ["localhost", "127.0.0.1"]:
    connect_args = {
        "ssl": {
            "ssl_mode": "REQUIRED"
        }
    }
    print("SSL Mode: REQUIRED")
else:
    print("SSL Mode: DISABLED (localhost)")

print("="*60)

# Tạo engine với connect_args
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,  # ← SSL config ở đây
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency để inject database session vào FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection function
def test_connection():
    """Test database connection"""
    import pymysql
    
    try:
        ssl_config = {"ssl_mode": "REQUIRED"} if DB_HOST not in ["localhost", "127.0.0.1"] else None
        
        conn = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl=ssl_config
        )
        
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return True, f"MySQL {version[0]}"
    except Exception as e:
        return False, str(e)

# Test khi chạy file trực tiếp
if __name__ == "__main__":
    print("="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60)
    
    success, message = test_connection()
    
    if success:
        print(f"Connected successfully!")
        print(f"Version: {message}")
    else:
        print(f"Connection failed!")
        print(f"Error: {message}")