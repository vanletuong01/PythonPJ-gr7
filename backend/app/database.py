from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306") 
DB_NAME = os.getenv("DB_NAME", "python_project")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
if DB_HOST != "localhost" and DB_HOST != "127.0.0.1":
    DATABASE_URL += "?ssl_mode=REQUIRED"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Kiểm tra connection trước khi dùng
    pool_recycle=3600,   # Recycle connection sau 1 giờ
    echo=False           # True để debug SQL queries
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """
    Test database connection
    """
    import pymysql
    
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl={'ssl_mode': 'REQUIRED'} if DB_HOST not in ['localhost', '127.0.0.1'] else None
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
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"Connection URL: {DATABASE_URL}")
    print("="*60)
    
    success, message = test_connection()
    
    if success:
        print(f"✅ Connected successfully!")
        print(f"📊 Version: {message}")
    else:
        print(f"❌ Connection failed!")
        print(f"Error: {message}")