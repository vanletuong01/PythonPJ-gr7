from pydantic import BaseModel

class LoginCreate(BaseModel):
    email: str
    phone: str = None
    name: str
    password: str

class LoginOut(BaseModel):
    id_login: int
    email: str
    phone: str = None
    name: str

    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    email: str
    password: str