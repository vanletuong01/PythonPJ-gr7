from fastapi import FastAPI
from backend.app.api.v1 import auth
from backend.app.api.v1 import class_api

app = FastAPI()
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(class_api.router, prefix="/api/v1/class", tags=["class"])