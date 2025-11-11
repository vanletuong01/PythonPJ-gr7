from sqlalchemy import Column, Integer, String
from backend.app.database import Base

class Type(Base):
    __tablename__ = "type"
    TypeID = Column(Integer, primary_key=True, index=True)
    TypeName = Column(String(100), nullable=False)
    