from pydantic import BaseModel

class TeacherCreate(BaseModel):
    username: str
    password: str
    full_name: str

class TeacherLogin(BaseModel):
    username: str
    password: str

class TeacherOut(BaseModel):
    id: int
    username: str
    full_name: str

    class Config:
        orm_mode = True