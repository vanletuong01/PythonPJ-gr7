
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys

# Core infrastructure
from backend.core.config import settings
from backend.core.logger import setup_logging, get_logger
from backend.core.exceptions import AppException, setup_exception_handlers

from backend.db import Database
from backend.db.config import API_HOST, API_PORT

from backend.api.auth_routes import router as auth_router
from backend.api.face_routes import router as face_router
from backend.api.health_routes import router as health_router

# Setup logging trước hết
setup_logging(
    log_level=settings.logs.level,
    log_format=settings.logs.format
)
logger = get_logger(__name__)

# Khởi tạo FastAPI app với production config
app = FastAPI(
    title=settings.api.title,
    version=settings.api.version,
    description=settings.api.description,
    docs_url="/api/docs" if not settings.api.debug else "/docs",
    redoc_url="/api/redoc" if not settings.api.debug else "/redoc",
    openapi_url="/api/openapi.json" if not settings.api.debug else "/openapi.json"
)

# CORS middleware - chặt chẽ trong production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins if settings.api.cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Request ID middleware for tracing
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req-{id(request)}")
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Setup exception handlers (toàn cục error handling)
setup_exception_handlers(app)

# Khởi tạo database
db = Database()

# Đăng ký các routes (Controllers)
app.include_router(health_router)  # Health checks ở root, không có prefix
app.include_router(auth_router)
app.include_router(face_router)
# app.include_router(student_router)
# app.include_router(attendance_router)
# app.include_router(stats_router)

# Test route để verify routing hoạt động
@app.get("/test")
async def test():
    return {"message": "Test route works"}

@app.post("/test-post")
async def test_post():
    return {"message": "Test POST works"}


@app.on_event("startup")
async def startup_event():
    """Kết nối database khi khởi động"""
    logger.info("🚀 API Server starting up...")
    
    try:
        # Kết nối database
        db.connect()
        logger.info("✅ Database connected successfully")
        
        # Log configuration
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.api.debug}")
        logger.info(f"Database: {settings.db.host}:{settings.db.port}/{settings.db.database}")
        logger.info(f"API: {settings.api.host}:{settings.api.port}")
        
        print("=" * 70)
        print(f"🎯 API Server đã khởi động thành công")
        print(f"📍 URL: http://{settings.api.host}:{settings.api.port}")
        print(f"📚 OpenAPI Docs: http://{settings.api.host}:{settings.api.port}/api/docs")
        print(f"❤️  Health: http://{settings.api.host}:{settings.api.port}/health")
        print(f"🔍 Readiness: http://{settings.api.host}:{settings.api.port}/health/ready")
        print(f"🏥 Liveness: http://{settings.api.host}:{settings.api.port}/health/live")
        print(f"\n📋 Environment: {settings.environment}")
        print(f"🔐 JWT Algorithm: {settings.jwt.algorithm}")
        print(f"💾 Upload Directory: {settings.files.upload_dir}")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Ngắt kết nối database khi tắt"""
    logger.info("🛑 API Server shutting down...")
    try:
        db.disconnect()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
    print("❌ API Server đã tắt")


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "Attendance System API - Production Ready",
        "version": settings.api.version,
        "status": "running",
        "environment": settings.environment,
        "documentation": {
            "openapi": "/api/docs",
            "redoc": "/api/redoc"
        },
        "health": {
            "status": "/health",
            "liveness": "/health/live",
            "readiness": "/health/ready"
        },
        "endpoints": {
            "authentication": "/api/auth",
            "face_recognition": "/api/face",
            "students": "/api/students",
            "attendance": "/api/attendance",
            "statistics": "/api/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )

