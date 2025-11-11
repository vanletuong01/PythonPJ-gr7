from sqlalchemy import Column, Integer, ForeignKey
from backend.app.database import Base

class Study(Base):
    __tablename__ = "study"
    StudyID = Column(Integer, primary_key=True, index=True)
    StudentID = Column(Integer, ForeignKey("student.StudentID"), nullable=False)
    ClassID = Column(Integer, ForeignKey("class.ClassID"), nullable=False)
    