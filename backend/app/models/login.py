from sqlalchemy import Column, Integer, String
from backend.app.database import Base

class Login(Base):
    __tablename__ = "login"
    id_login = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), unique=True, index=True)
    phone = Column(String(10))
    name = Column(String(100))
    pass_field = Column("pass", String(100))  