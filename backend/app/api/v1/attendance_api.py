from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import pymysql
import traceback
from datetime import datetime, date
from backend.app.models.student import Student
from backend.app.models.study import Study
from pydantic import BaseModel
from backend.app.models.attendance import Attendance
from sqlalchemy.orm import Session
from backend.app.database import get_db


router = APIRouter()

# ===== THÊM PHẦN NÀY =====
class ManualAttendanceRequest(BaseModel):
    study_id: int
    session_date: date  # format: "2025-11-17"

# ===== HẾT PHẦN THÊM =====

def get_study_id(student_id, class_id):
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="python_project",
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT StudyID FROM study WHERE StudentID=%s AND ClassID=%s",
        (student_id, class_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

@router.post("/recognize")
async def recognize_attendance(
    file: UploadFile = File(...),
    class_id: int = Form(...),
):
    """Nhận diện khuôn mặt cho điểm danh"""
    try:
        # Đọc ảnh
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Không đọc được ảnh"}
            )
        
        # Gọi smart_face_attendance
        from backend.app.ai.smart_face_attendance import match_image_and_check_real, save_attendance_to_db
        
        result = match_image_and_check_real(img)
        
        print("DEBUG result:", result)
        
        if result.get('status') != 'ok':
            return JSONResponse(
                status_code=400,
                content=result
            )
        
        if not result.get('found'):
            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "message": "Không khớp với sinh viên nào"
                }
            )
        
        if not result.get('is_real'):
            return JSONResponse(
                status_code=403,
                content={
                    "status": "fake",
                    "message": "Ảnh nghi ngờ giả mạo",
                    "real_conf": result.get('real_conf')
                }
            )
        
        # Lưu điểm danh
        student = result.get('student', {})
        student_id = student.get('id')
        if not student_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Không lấy được StudentID"}
            )
        
        print("DEBUG student_id:", student_id, "class_id:", class_id)
        
        study_id = get_study_id(student_id, class_id)
        if not study_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Sinh viên chưa thuộc lớp này!"}
            )
        
        print("DEBUG study_id:", study_id)
        
        print("DEBUG save_attendance_to_db input:", study_id, result.get('similarity'))
        
        save_attendance_to_db(
            study_id,
            result.get('similarity')
        )
        
        return {
            "status": "ok",
            "student": student,
            "similarity": result.get('similarity'),
            "real_conf": result.get('real_conf'),
            "message": "✅ Điểm danh thành công"
        }
        
    except Exception as e:
        print("ERROR in recognize_attendance:", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Lỗi server: {str(e)}"
            }
        )

# ===== API LẤY CHI TIẾT BUỔI HỌC =====
@router.get("/session-detail/{class_id}/{session_date}")
def get_session_detail(class_id: int, session_date: str, db: Session = Depends(get_db)):
    """
    Lấy chi tiết buổi học:
    - Tổng sinh viên đã điểm danh
    - Tổng sinh viên vắng
    - Danh sách sinh viên (có thời gian điểm danh nếu có)
    """
    # Chuyển string -> date
    try:
        session_date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
    except:
        raise HTTPException(status_code=400, detail="Ngày không hợp lệ (format: YYYY-MM-DD)")
    
    # Lấy danh sách sinh viên trong lớp
    students = (
        db.query(
            Student.StudentID,
            Student.FullName,
            Student.StudentCode,
            Study.StudyID,
            Attendance.Time.label("AttendanceTime"),
            Attendance.AttendanceID
        )
        .join(Study, Study.StudentID == Student.StudentID)
        .outerjoin(
            Attendance,
            (Attendance.StudyID == Study.StudyID) & (Attendance.Date == session_date_obj)
        )
        .filter(Study.ClassID == class_id)
        .all()
    )
    
    attended = []
    absent = []
    
    for s in students:
        student_info = {
            "StudentID": s.StudentID,
            "FullName": s.FullName,
            "StudentCode": s.StudentCode,
            "StudyID": s.StudyID,
            "AttendanceTime": s.AttendanceTime.strftime("%H:%M:%S") if s.AttendanceTime else None,
            "Status": "Có mặt" if s.AttendanceID else "Vắng"
        }
        
        if s.AttendanceID:
            attended.append(student_info)
        else:
            absent.append(student_info)
    
    return {
        "success": True,
        "session_date": session_date,
        "total_students": len(students),
        "total_attended": len(attended),
        "total_absent": len(absent),
        "attended_list": attended,
        "absent_list": absent
    }

# ===== API ĐIỂM DANH THỦ CÔNG =====
@router.post("/manual-checkin")
def manual_checkin(
    study_id: int,
    session_date: str,
    db: Session = Depends(get_db)
):
    """
    Điểm danh thủ công (không lưu Time và PhotoPath)
    """
    try:
        # Chuyển đổi string date sang date object
        try:
            date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Kiểm tra đã điểm danh chưa
        existing = db.query(Attendance).filter(
            Attendance.StudyID == study_id,
            Attendance.Date == date_obj
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": "Sinh viên đã được điểm danh rồi"
            }
        
        # Tạo bản ghi mới (Time=NULL, PhotoPath=NULL)
        new_attendance = Attendance(
            StudyID=study_id,
            Date=date_obj,
            Time=None,  # Không lưu thời gian
            PhotoPath=None  # Không lưu ảnh
        )
        
        db.add(new_attendance)
        db.commit()
        db.refresh(new_attendance)
        
        return {
            "success": True,
            "message": "Điểm danh thành công",
            "attendance_id": new_attendance.AttendanceID
        }
        
    except Exception as e:
        db.rollback()
        print(f"Lỗi điểm danh thủ công: {e}")
        raise HTTPException(status_code=500, detail=str(e))