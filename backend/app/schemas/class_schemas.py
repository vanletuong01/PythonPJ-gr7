from pydantic import BaseModel
from datetime import date

class ClassCreate(BaseModel):
    quantity: int
    rank: str = None
    semester: str
    date_start: date
    date_end: date
    session: str
    class_name: str
    full_class_name: str
    teacher_class: str
    type_id: int
    major_id: int
    shift_id: int

class ClassOut(BaseModel):
    ClassID: int
    class_name: str
    full_class_name: str

    class Config:
        from_attributes = True