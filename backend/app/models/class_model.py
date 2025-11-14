from sqlalchemy import Column, Integer, String, Date, ForeignKey
from backend.app.database import Base

class Class(Base):
    __tablename__ = "class"
    
    ClassID = Column(Integer, primary_key=True, autoincrement=True)
    Quantity = Column(Integer)
    Rank = Column(String(50), nullable=True)
    Semester = Column(String(45))
    DateStart = Column(Date)
    DateEnd = Column(Date)
    Session = Column(String(45), nullable=True)
    ClassName = Column(String(100))
    FullClassName = Column(String(200), nullable=True)
    Teacher_class = Column(String(100), nullable=True)
    TypeID = Column(Integer, ForeignKey("type.TypeID"))
    MajorID = Column(Integer, ForeignKey("major.MajorID"))
    ShiftID = Column(Integer, ForeignKey("shift.ShiftID"))