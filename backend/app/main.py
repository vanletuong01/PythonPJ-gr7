import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.app.api.v1 import auth, class_api, student ,major_api, type_api

app = FastAPI(
    title="VAA API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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

@app.get("/")
def root():
    return {"message": "VAA API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(class_api.router, prefix="/api/v1/class", tags=["class"])
app.include_router(student.router, prefix="/api/v1/student", tags=["student"])
app.include_router(major_api.router, prefix="/api/v1/major", tags=["major"])
app.include_router(type_api.router, prefix="/api/v1/type", tags=["type"])
