"""
Attendance API Routes - Controller layer cho điểm danh
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import date

from db import Database
from utils.face_recognition import FaceRecognition
from services.attendance_service import AttendanceService

# Khởi tạo router
router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)

# Khởi tạo dependencies
db = Database()
face_rec = FaceRecognition()
attendance_service = AttendanceService(db, face_rec)


@router.post("/checkin")
async def check_attendance(
    image: UploadFile = File(...),
    attendance_date: Optional[str] = Form(None)
):
    """
    Điểm danh bằng ảnh khuôn mặt
    - Upload ảnh
    - Trích xuất embedding
    - So sánh với database
    - Lưu kết quả điểm danh
    """
    try:
        result = attendance_service.check_in_attendance(
            image=image,
            attendance_date=attendance_date
        )
        
        return JSONResponse(status_code=200, content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/today")
async def get_today_attendance():
    """Lấy danh sách điểm danh hôm nay"""
    try:
        attendance_list = attendance_service.get_today_attendance()
        
        return JSONResponse(
            status_code=200,
            content={
                "date": str(date.today()),
                "total": len(attendance_list),
                "attendance": attendance_list
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/student/{student_id}")
async def get_student_attendance(student_id: str):
    """Lấy lịch sử điểm danh của sinh viên"""
    try:
        attendance_list = attendance_service.get_student_attendance_history(student_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "student_id": student_id,
                "total": len(attendance_list),
                "attendance": attendance_list
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
