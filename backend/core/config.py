"""
Centralized Config Management
Load từ environment variables + .env file
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os
from dotenv import load_dotenv

# ✅ Luôn load .env từ thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)
print(f"✅ Loaded .env from: {env_path}")

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    host: str = Field(default="localhost", env="DB_HOST")
    user: str = Field(default="root", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    database: str = Field(default="python_project", env="DB_NAME")
    port: int = Field(default=3306, env="DB_PORT")
    
    @property
    def url(self) -> str:
        """Connection URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class APISettings(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    title: str = "Attendance System API"
    version: str = "2.0.0"
    description: str = "Hệ thống điểm danh sinh viên - Architecture MVC"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class ModelSettings(BaseSettings):
    """ML Model configuration"""
    embedding_dim: int = Field(default=512, env="EMBEDDING_DIM")
    confidence_threshold: float = Field(default=0.6, env="CONFIDENCE_THRESHOLD")
    max_face_distance: float = Field(default=0.6, env="MAX_FACE_DISTANCE")
    face_size: int = Field(default=112, env="FACE_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class FileSettings(BaseSettings):
    """File upload configuration"""
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    student_images_dir: str = Field(default="uploads/student_images", env="STUDENT_IMAGES_DIR")
    attendance_images_dir: str = Field(default="uploads/attendance_images", env="ATTENDANCE_IMAGES_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: list = ["jpg", "jpeg", "png"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class JWTSettings(BaseSettings):
    """JWT configuration"""
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=43200, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 30 days
    
    @validator("secret_key", pre=True)
    def validate_secret_key(cls, v):
        if v == "dev-secret-key-change-in-production" and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("SECRET_KEY must be changed in production!")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class RedisSettings(BaseSettings):
    """Redis configuration (optional)"""
    enabled: bool = Field(default=False, env="REDIS_ENABLED")
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    ttl: int = Field(default=3600, env="REDIS_TTL")  # 1 hour
    
    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class LogSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")  # 'json' or 'text'
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class Settings(BaseSettings):
    """Centralized settings"""
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Sub-settings
    db: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    models: ModelSettings = ModelSettings()
    files: FileSettings = FileSettings()
    jwt: JWTSettings = JWTSettings()
    redis: RedisSettings = RedisSettings()
    logs: LogSettings = LogSettings()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()

# Print config on startup (hide secrets)
if __name__ == "__main__":
    print(f"Environment: {settings.environment}")
    print(f"API: {settings.api.host}:{settings.api.port}")
    print(f"Database: {settings.db.host}:{settings.db.port}/{settings.db.database}")
    print(f"Models: {settings.models.embedding_dim}D embeddings, threshold={settings.models.confidence_threshold}")
    print(f"Redis: {'Enabled' if settings.redis.enabled else 'Disabled'}")
    print(f"Logging: {settings.logs.level} ({settings.logs.format})")
