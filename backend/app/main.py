import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1 import auth, class_api, student_api, major_api, type_api, capture_api ,attendance_api ,recognize_api

import logging

# Bật logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VAA API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.streamlit.app",      # Streamlit Cloud
        "http://localhost:8501",        # Local Streamlit
        "https://*.onrender.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    print(f">>> {request.method} {request.url.path}")
    response = await call_next(request)
    dur = (time.time() - start) * 1000
    print(f"<<< {request.method} {request.url.path} {int(dur)}ms status={response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url.path} → {exc!r}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": str(exc)}
    )

# Đăng ký router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(class_api.router, prefix="/api/v1/class", tags=["class"])
app.include_router(student_api.router, prefix="/api/v1/student", tags=["student"])
app.include_router(major_api.router, prefix="/api/v1/major", tags=["major"])
app.include_router(type_api.router, prefix="/api/v1/type", tags=["type"])
app.include_router(capture_api.router, prefix="/api/v1/capture", tags=["capture"])
app.include_router(attendance_api.router, prefix="/api/v1/attendance", tags=["attendance"])
app.include_router(recognize_api.router, prefix="/api/v1/ai", tags=["ai"])

print("🔥 Registered routes:")
for route in app.routes:
    print(f"  - {route.path} [{route.methods if hasattr(route, 'methods') else 'N/A'}]")

@app.get("/")
def root():
    return {"message": "VAA API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

