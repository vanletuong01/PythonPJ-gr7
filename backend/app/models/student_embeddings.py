from sqlalchemy import Column, Integer, String, Float, LargeBinary, ForeignKey, TIMESTAMP
from backend.app.database import Base

class StudentEmbeddings(Base):
    __tablename__ = "student_embeddings"
    EmbeddingID = Column(Integer, primary_key=True, index=True)
    StudentID = Column(Integer, ForeignKey("student.StudentID"), nullable=False)
    Embedding = Column(LargeBinary, nullable=False)
    EmbeddingDim = Column(Integer, nullable=False)
    PhotoPath = Column(String(1024))
    Quality = Column(Float)
    Source = Column(String(100))
    CreatedAt = Column(TIMESTAMP, nullable=False)
    