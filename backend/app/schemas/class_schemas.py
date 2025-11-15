class ClassOut(BaseModel):
    ClassID: int
    ClassName: str
    FullClassName: str | None = None
    Teacher_class: str | None = None
    Quantity: int
    Semester: str
    DateStart: date
    DateEnd: date
    Session: str | None = None
    CourseCode: int | None = None      # ← THÊM

    model_config = ConfigDict(from_attributes=True)
