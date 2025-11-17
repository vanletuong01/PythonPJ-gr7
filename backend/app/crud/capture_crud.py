# backend/app/crud/capture_crud.py

from sqlalchemy.orm import Session
from backend.app.models.student import Student
import numpy as np
import pickle
from pathlib import Path
from backend.app.embeddings_db import insert_embedding

# Nếu có bảng face_embeddings riêng
# from backend.app.models.face_embedding import FaceEmbedding

def create_or_get_student(db: Session, student_code: str, full_name: str):
    student = db.query(Student).filter_by(StudentCode=student_code).first()

    if student:
        return student.StudentID

    new_stu = Student(
        FullName=full_name,
        StudentCode=student_code,
        PhotoStatus="pending",
        MajorID=1,
        TypeID=1
    )

    db.add(new_stu)
    db.commit()
    db.refresh(new_stu)

    return new_stu.StudentID


def update_student_photo(db: Session, student_code: str, photo_path: str):
    student = db.query(Student).filter_by(StudentCode=student_code).first()
    student.PhotoStatus = "done"
    student.StudentPhoto = photo_path
    db.commit()


def save_embedding(student_code: str, emb, full_name: str, folder_path: str):
    insert_embedding(student_code=student_code, embedding=emb, photo_path=folder_path, full_name=full_name)


def save_best_embedding(
    db: Session,
    student_id: int,
    embedding: np.ndarray,
    image_path: str,
    quality_score: float
) -> int:
    """
    Lưu embedding vào DB.
    
    Option 1: Lưu vào bảng riêng face_embeddings
    Option 2: Lưu vào Student.Embedding (pickle blob)
    """
    
    # Option 1: Nếu có bảng face_embeddings
    # face_emb = FaceEmbedding(
    #     StudentID=student_id,
    #     Embedding=pickle.dumps(embedding),
    #     ImagePath=image_path,
    #     QualityScore=quality_score
    # )
    # db.add(face_emb)
    # db.commit()
    # return face_emb.EmbeddingID
    
    # Option 2: Lưu vào Student (tạm thời)
    stu = db.query(Student).filter(Student.StudentID == student_id).first()
    if stu:
        # Giả sử Student có column Embedding (BLOB)
        # stu.Embedding = pickle.dumps(embedding)
        # stu.BestImagePath = image_path
        # stu.QualityScore = quality_score
        db.commit()
    
    # Hoặc lưu vào file pickle
    pkl_path = Path(image_path).parent / "embedding.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump({
            "embedding": embedding,
            "image_path": image_path,
            "quality_score": quality_score
        }, f)
    
    return student_id
