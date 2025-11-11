from sqlalchemy import Column, Integer, String, Time
from backend.app.database import Base

class Shift(Base):
    __tablename__ = "shift"
    ShiftID = Column(Integer, primary_key=True, index=True)
    ShiftName = Column(String(50), nullable=False)
    TimeStart = Column(Time, nullable=False)
    TimeEnd = Column(Time, nullable=False)
