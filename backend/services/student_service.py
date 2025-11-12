"""
Student Service - Business logic cho quản lý sinh viên
"""
from typing import Optional, List
import os
import uuid
from fastapi import UploadFile, HTTPException

from backend.db.database import Database
from backend.utils.face_recognition import FaceRecognition
from backend.db.config import STUDENT_IMAGES_DIR


class StudentService:
    """Service xử lý logic nghiệp vụ liên quan đến sinh viên"""
    
    def __init__(self, db: Database, face_rec: FaceRecognition):
        self.db = db
        self.face_rec = face_rec
    
    def check_student_exists(self, student_id: str) -> bool:
        """Kiểm tra sinh viên đã tồn tại chưa"""
        existing = self.db.fetch_one(
            "SELECT * FROM students WHERE student_id = %s",
            (student_id,)
        )
        return existing is not None
    
    def save_student_image(self, student_id: str, image: UploadFile) -> str:
        """Lưu ảnh sinh viên vào server"""
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"{student_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(STUDENT_IMAGES_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(image.file, buffer)
        
        return file_path
    
    def register_student(
        self,
        student_id: str,
        full_name: str,
        class_name: str,
        email: Optional[str],
        phone: Optional[str],
        image: UploadFile
    ) -> dict:
        """
        Đăng ký sinh viên mới
        - Kiểm tra tồn tại
        - Lưu ảnh
        - Trích xuất embedding
        - Lưu vào database
        """
        # Kiểm tra sinh viên đã tồn tại
        if self.check_student_exists(student_id):
            raise HTTPException(status_code=400, detail="Mã sinh viên đã tồn tại")
        
        # Lưu ảnh
        file_path = self.save_student_image(student_id, image)
        
        try:
            # Trích xuất embedding
            embedding = self.face_rec.extract_embedding_from_path(file_path)
            if embedding is None:
                os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="Không phát hiện khuôn mặt trong ảnh"
                )
            
            # Lưu thông tin sinh viên
            self.db.execute_query(
                """INSERT INTO students (student_id, full_name, class_name, email, phone, image_path)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (student_id, full_name, class_name, email, phone, file_path)
            )
            
            # Lưu embedding
            embedding_bytes = self.face_rec.serialize_embedding(embedding)
            self.db.execute_query(
                """INSERT INTO face_embeddings (student_id, embedding, image_path)
                   VALUES (%s, %s, %s)""",
                (student_id, embedding_bytes, file_path)
            )
            
            return {
                "message": "Đăng ký sinh viên thành công",
                "student_id": student_id,
                "full_name": full_name
            }
            
        except HTTPException:
            raise
        except Exception as e:
            # Rollback: xóa ảnh nếu có lỗi
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
    def get_all_students(self) -> List[dict]:
        """Lấy danh sách tất cả sinh viên"""
        students = self.db.fetch_all("SELECT * FROM students ORDER BY created_at DESC")
        return students or []
    
    def get_student_by_id(self, student_id: str) -> Optional[dict]:
        """Lấy thông tin sinh viên theo mã"""
        student = self.db.fetch_one(
            "SELECT * FROM students WHERE student_id = %s",
            (student_id,)
        )
        return student
    
    def delete_student(self, student_id: str) -> dict:
        """Xóa sinh viên"""
        student = self.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
        
        # Xóa ảnh
        if student['image_path'] and os.path.exists(student['image_path']):
            os.remove(student['image_path'])
        
        # Xóa khỏi database (cascade sẽ xóa embeddings và attendance)
        self.db.execute_query(
            "DELETE FROM students WHERE student_id = %s",
            (student_id,)
        )
        
        return {"message": f"Đã xóa sinh viên {student['full_name']}"}
    
    def get_total_students(self) -> int:
        """Đếm tổng số sinh viên"""
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM students")
        return result['count'] if result else 0
