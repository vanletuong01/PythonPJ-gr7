"""
Configuration - Load from environment variables (.env)
Support for MySQL, file uploads, and API server setup.
"""

import os
from pathlib import Path

# Optional dependency: python-dotenv is recommended for local development
# but the code should still run when it's not installed (e.g., in production
# environments that provide environment variables through other means).
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
    print("⚠️  python-dotenv not installed; skipping .env loading. To enable, run: pip install python-dotenv")

# =========================================================
# 1️⃣ Base setup
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load biến môi trường từ file .env nếu có
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print("⚠️  Warning: .env file not found, using default values.")

# =========================================================
# 2️⃣ Database configuration
# =========================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "python_project"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

# =========================================================
# 3️⃣ File upload configuration
# =========================================================
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
STUDENT_IMAGES_DIR = BASE_DIR / os.getenv("STUDENT_IMAGES_DIR", "uploads/student_images")
ATTENDANCE_IMAGES_DIR = BASE_DIR / os.getenv("ATTENDANCE_IMAGES_DIR", "uploads/attendance_images")

# Tạo thư mục nếu chưa có
for path in [UPLOAD_DIR, STUDENT_IMAGES_DIR, ATTENDANCE_IMAGES_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# =========================================================
# 4️⃣ Face recognition parameters
# =========================================================
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
MAX_FACE_DISTANCE = float(os.getenv("MAX_FACE_DISTANCE", 0.6))

# =========================================================
# 5️⃣ File upload limits
# =========================================================
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png").split(",")

# =========================================================
# 6️⃣ API Configuration
# =========================================================
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))

# =========================================================
# 7️⃣ JWT Configuration
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-vaa-2025-secure-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30))  # 30 days

# =========================================================
# 8️⃣ Optional logging
# =========================================================
print("✅ Loaded configuration:")
print(f"   - DB: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
print(f"   - Uploads: {UPLOAD_DIR}")
print(f"   - API: {API_HOST}:{API_PORT}")
