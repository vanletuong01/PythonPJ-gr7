from sqlalchemy import Column, Integer, String, Date, ForeignKey
from backend.app.database import Base

class Class(Base):
    __tablename__ = "class"
    ClassID = Column(Integer, primary_key=True, index=True)
    Quantity = Column(Integer, nullable=False)
    Rank = Column(String(50))
    Semester = Column(String(45), nullable=False)
    DateStart = Column(Date, nullable=False)
    DateEnd = Column(Date, nullable=False)
    Session = Column(String(45))
    ClassName = Column(String(100), nullable=False)
    FullClassName = Column(String(200))
    Teacher_class = Column(String(100))
    TypeID = Column(Integer, ForeignKey("type.TypeID"), nullable=False)
    MajorID = Column(Integer, ForeignKey("major.MajorID"), nullable=False)
    ShiftID = Column(Integer, ForeignKey("shift.ShiftID"), nullable=False)