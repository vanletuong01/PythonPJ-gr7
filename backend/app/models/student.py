from sqlalchemy import Column, Integer, String, Date
from backend.app.database import Base

class Student(Base):
    __tablename__ = "student"
    StudentID = Column(Integer, primary_key=True, index=True)
    FullName = Column(String(100), nullable=False)
    StudentCode = Column(String(20), nullable=False)
    DefaultClass = Column(String(45))
    Phone = Column(String(20))
    AcademicYear = Column(String(10))
    DateOfBirth = Column(Date)
    CitizenID = Column(String(20))
    PhotoStatus = Column(String(10))
    StudentPhoto = Column(String(255))
    MajorID = Column(Integer, nullable=False)
    TypeID = Column(Integer, nullable=False)