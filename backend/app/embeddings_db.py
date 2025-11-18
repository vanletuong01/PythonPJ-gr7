# backend/app/embeddings_db.py

from datetime import datetime
import numpy as np
import pickle
from sqlalchemy.orm import Session
from backend.app.models.student_embeddings import StudentEmbeddings

def insert_embedding(
    db: Session,
    student_id: int,
    embedding: np.ndarray,
    photo_path: str,
    quality: float,
    source: str,
):
    """
    Lưu embedding vào bảng student_embeddings
    """

    # convert numpy -> bytes (pickle)
    emb_bytes = pickle.dumps(embedding.astype(np.float32))

    record = StudentEmbeddings(
        StudentID=student_id,
        Embedding=emb_bytes,
        EmbeddingDim=len(embedding),
        PhotoPath=photo_path,
        Quality=float(quality),
        Source=source,
        CreatedAt=datetime.now(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record.EmbeddingID
