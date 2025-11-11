"""
Attendance Service - Business logic cho điểm danh
"""
from typing import Optional, List, Tuple
import os
import uuid
from datetime import datetime, date
from fastapi import UploadFile, HTTPException

from db import Database
from utils.face_recognition import FaceRecognition
from config import ATTENDANCE_IMAGES_DIR, CONFIDENCE_THRESHOLD


class AttendanceService:
    """Service xử lý logic nghiệp vụ liên quan đến điểm danh"""
    
    def __init__(self, db: Database, face_rec: FaceRecognition):
        self.db = db
        self.face_rec = face_rec
    
    def save_attendance_image(self, image: UploadFile) -> str:
        """Lưu ảnh điểm danh vào server"""
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(ATTENDANCE_IMAGES_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(image.file, buffer)
        
        return file_path
    
    def get_all_face_embeddings(self) -> List[Tuple[int, bytes]]:
        """Lấy tất cả embeddings từ database"""
        all_embeddings = self.db.fetch_all(
            "SELECT id, student_id, embedding FROM face_embeddings"
        )
        
        if not all_embeddings:
            return []
        
        # Chuyển đổi embeddings
        stored_embeddings = [
            (row['id'], self.face_rec.deserialize_embedding(row['embedding']))
            for row in all_embeddings
        ]
        
        return stored_embeddings
    
    def find_matching_student(self, query_embedding) -> Tuple[Optional[str], float]:
        """
        Tìm sinh viên khớp với embedding
        
        Returns:
            Tuple of (student_id, confidence_score)
        """
        stored_embeddings = self.get_all_face_embeddings()
        
        if not stored_embeddings:
            raise HTTPException(
                status_code=404,
                detail="Chưa có sinh viên nào được đăng ký"
            )
        
        # Tìm match tốt nhất
        best_id, confidence = self.face_rec.find_best_match(query_embedding, stored_embeddings)
        
        if confidence < CONFIDENCE_THRESHOLD:
            return None, confidence
        
        # Lấy student_id từ embedding_id
        embedding_info = self.db.fetch_one(
            "SELECT student_id FROM face_embeddings WHERE id = %s",
            (best_id,)
        )
        
        return embedding_info['student_id'], confidence
    
    def check_already_attended(self, student_id: str, attendance_date: date) -> Optional[dict]:
        """Kiểm tra sinh viên đã điểm danh chưa"""
        return self.db.fetch_one(
            """SELECT * FROM attendance 
               WHERE student_id = %s AND attendance_date = %s""",
            (student_id, attendance_date)
        )
    
    def check_in_attendance(
        self,
        image: UploadFile,
        attendance_date: Optional[str] = None
    ) -> dict:
        """
        Điểm danh bằng ảnh khuôn mặt
        
        Returns:
            dict với thông tin kết quả điểm danh
        """
        # Lưu ảnh tạm
        file_path = self.save_attendance_image(image)
        
        try:
            # Trích xuất embedding
            query_embedding = self.face_rec.extract_embedding_from_path(file_path)
            if query_embedding is None:
                os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="Không phát hiện khuôn mặt trong ảnh"
                )
            
            # Tìm sinh viên khớp
            student_id, confidence = self.find_matching_student(query_embedding)
            
            if student_id is None:
                os.remove(file_path)
                return {
                    "success": False,
                    "message": "Không nhận diện được khuôn mặt",
                    "confidence": float(confidence)
                }
            
            # Lấy thông tin sinh viên
            student = self.db.fetch_one(
                "SELECT * FROM students WHERE student_id = %s",
                (student_id,)
            )
            
            # Xác định ngày điểm danh
            if attendance_date:
                att_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            else:
                att_date = date.today()
            
            # Kiểm tra đã điểm danh chưa
            existing_attendance = self.check_already_attended(student_id, att_date)
            
            if existing_attendance:
                os.remove(file_path)
                return {
                    "success": False,
                    "message": f"Sinh viên {student['full_name']} đã điểm danh hôm nay",
                    "student": {
                        "student_id": student['student_id'],
                        "full_name": student['full_name'],
                        "class_name": student['class_name']
                    },
                    "attendance_time": str(existing_attendance['attendance_time'])
                }
            
            # Lưu điểm danh
            current_time = datetime.now().time()
            self.db.execute_query(
                """INSERT INTO attendance 
                   (student_id, attendance_date, attendance_time, confidence_score, image_path)
                   VALUES (%s, %s, %s, %s, %s)""",
                (student_id, att_date, current_time, confidence, file_path)
            )
            
            return {
                "success": True,
                "message": "Điểm danh thành công",
                "student": {
                    "student_id": student['student_id'],
                    "full_name": student['full_name'],
                    "class_name": student['class_name']
                },
                "attendance_time": str(current_time),
                "confidence": float(confidence)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
    def get_today_attendance(self) -> List[dict]:
        """Lấy danh sách điểm danh hôm nay"""
        today = date.today()
        attendance_list = self.db.fetch_all(
            """SELECT a.*, s.full_name, s.class_name 
               FROM attendance a
               JOIN students s ON a.student_id = s.student_id
               WHERE a.attendance_date = %s
               ORDER BY a.attendance_time DESC""",
            (today,)
        )
        return attendance_list or []
    
    def get_student_attendance_history(self, student_id: str) -> List[dict]:
        """Lấy lịch sử điểm danh của sinh viên"""
        attendance_list = self.db.fetch_all(
            """SELECT a.*, s.full_name, s.class_name 
               FROM attendance a
               JOIN students s ON a.student_id = s.student_id
               WHERE a.student_id = %s
               ORDER BY a.attendance_date DESC, a.attendance_time DESC""",
            (student_id,)
        )
        return attendance_list or []
    
    def get_attendance_count_today(self) -> int:
        """Đếm số lượng điểm danh hôm nay"""
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM attendance WHERE attendance_date = %s",
            (date.today(),)
        )
        return result['count'] if result else 0
