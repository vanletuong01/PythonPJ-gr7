from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Database
from config import API_HOST, API_PORT

# Import các routes (Controllers)
# from api import student_router, attendance_router, stats_router, auth_router
from api.auth_routes import router as auth_router
# from api.student_routes import router as student_router
# from api.attendance_routes import router as attendance_router
# from api.stats_routes import router as stats_router

# Khởi tạo FastAPI app
app = FastAPI(
    title="Attendance System API",
    version="2.0.0",
    description="Hệ thống điểm danh sinh viên"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo database
db = Database()

# Đăng ký các routes (Controllers) - router đã có prefix="/api/auth" trong auth_routes.py
app.include_router(auth_router)
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
    db.connect()
    print("=" * 60)
    print("API Server đã khởi động")
    print(f"Kiến trúc: MVC Pattern")
    print(f"URL: http://{API_HOST}:{API_PORT}")
    print(f"Docs: http://{API_HOST}:{API_PORT}/docs")
    print("\nRoutes đã đăng ký:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)[0] if route.methods else 'GET':<6} {route.path}")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Ngắt kết nối database khi tắt"""
    db.disconnect()
    print("API Server đã tắt")


@app.get("/")
async def root():
    """Endpoint kiểm tra API"""
    return {
        "message": "Attendance System API",
        "version": "2.0.0",
        "architecture": "MVC Pattern",
        "status": "running",
        "endpoints": {
            "students": "/api/students",
            "attendance": "/api/attendance",
            "stats": "/api/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
