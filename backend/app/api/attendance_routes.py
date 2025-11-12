from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import date
from services.attendance_service import AttendanceService

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
attendance_service = AttendanceService()

@router.post("/checkin")
async def check_attendance(
    image: UploadFile = File(...),
    attendance_date: Optional[str] = Form(None)
):
    try:
        result = await attendance_service.mark_attendance(image)
        return JSONResponse(status_code=200, content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today")
async def get_today_attendance():
    try:
        data = attendance_service.get_today_attendance()
        return {
            "date": str(date.today()),
            "total": len(data),
            "attendance": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{student_id}")
async def get_student_attendance(student_id: str):
    try:
        data = attendance_service.get_student_history(student_id)
        return {
            "student_id": student_id,
            "total": len(data),
            "attendance": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
