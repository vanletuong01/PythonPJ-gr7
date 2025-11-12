"""
Stats API Routes - Controller layer cho thống kê
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import date

from db import Database
from services.student_service import StudentService
from services.attendance_service import AttendanceService
from utils.face_recognition import FaceRecognition

# Khởi tạo router
router = APIRouter(
    prefix="/api/stats",
    tags=["Statistics"]
)

# Khởi tạo dependencies
db = Database()
face_rec = FaceRecognition()
student_service = StudentService(db, face_rec)
attendance_service = AttendanceService(db, face_rec)


@router.get("")
async def get_statistics():
    """Lấy thống kê tổng quan"""
    try:
        total_students = student_service.get_total_students()
        attendance_today = attendance_service.get_attendance_count_today()
        
        return JSONResponse(
            status_code=200,
            content={
                "total_students": total_students,
                "attendance_today": attendance_today,
                "date": str(date.today())
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
