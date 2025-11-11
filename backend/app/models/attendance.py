from sqlalchemy import Column, Integer, Date, Time, String, ForeignKey
from backend.app.database import Base

class Attendance(Base):
    __tablename__ = "attendance"
    AttendanceID = Column(Integer, primary_key=True, index=True)
    StudyID = Column(Integer, ForeignKey("study.StudyID"), nullable=False)
    Date = Column(Date, nullable=False)
    Time = Column(Time, nullable=False)
    PhotoPath = Column(String(255))
