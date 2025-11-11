from sqlalchemy import Column, Integer, String
from backend.app.database import Base

class Major(Base):
    __tablename__ = "major"
    MajorID = Column(Integer, primary_key=True, index=True)
    MajorName = Column(String(100), nullable=False)
    Full_name_mj = Column(String(500))
    