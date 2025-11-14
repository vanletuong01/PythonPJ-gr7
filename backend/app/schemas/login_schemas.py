from pydantic import BaseModel, EmailStr, ConfigDict

class LoginCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginOut(BaseModel):
    id_login: int
    email: EmailStr
    name: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)