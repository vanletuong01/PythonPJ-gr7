from sqlalchemy import Column, Integer, ForeignKey
from backend.app.database import Base

class Teach(Base):
    __tablename__ = "teach"
    id_teach = Column(Integer, primary_key=True, index=True)
    id_login = Column(Integer, ForeignKey("login.id_login"))
    ClassID = Column(Integer, ForeignKey("class.ClassID"))
    