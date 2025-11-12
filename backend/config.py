"""
Configuration - Load from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file từ thư mục gốc project
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "attendance_system"),
    "port": int(os.getenv("DB_PORT", 3307))
}

# File upload configuration
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
STUDENT_IMAGES_DIR = BASE_DIR / os.getenv("STUDENT_IMAGES_DIR", "uploads/student_images")
ATTENDANCE_IMAGES_DIR = BASE_DIR / os.getenv("ATTENDANCE_IMAGES_DIR", "uploads/attendance_images")

# Tạo thư mục nếu chưa tồn tại
STUDENT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ATTENDANCE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Face recognition configuration
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
MAX_FACE_DISTANCE = float(os.getenv("MAX_FACE_DISTANCE", 0.6))

# File upload limits
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png").split(",")

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-123456")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 43200))  # 30 days
