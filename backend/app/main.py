from fastapi import FastAPI
from backend.app.api.v1 import auth

app = FastAPI()
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])