"""
Student API Routes - Controller layer cho quản lý sinh viên
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from db import Database
from utils.face_recognition import FaceRecognition
from services.student_service import StudentService
from models.schemas import StudentListResponse, StudentResponse

# Khởi tạo router
router = APIRouter(
    prefix="/api/students",
    tags=["Students"]
)

# Khởi tạo dependencies
db = Database()
face_rec = FaceRecognition()
student_service = StudentService(db, face_rec)


@router.post("/register")
async def register_student(
    student_id: str = Form(...),
    full_name: str = Form(...),
    class_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """
    Đăng ký sinh viên mới
    - Upload ảnh lên server
    - Trích xuất face embedding
    - Lưu thông tin vào database
    """
    try:
        result = student_service.register_student(
            student_id=student_id,
            full_name=full_name,
            class_name=class_name,
            email=email,
            phone=phone,
            image=image
        )
        
        return JSONResponse(
            status_code=201,
            content=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("")
async def get_all_students():
    """Lấy danh sách tất cả sinh viên"""
    try:
        students = student_service.get_all_students()
        return JSONResponse(
            status_code=200,
            content={
                "total": len(students),
                "students": students
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/{student_id}")
async def get_student(student_id: str):
    """Lấy thông tin chi tiết sinh viên"""
    try:
        student = student_service.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
        
        return JSONResponse(status_code=200, content=student)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.delete("/{student_id}")
async def delete_student(student_id: str):
    """Xóa sinh viên"""
    try:
        result = student_service.delete_student(student_id)
        return JSONResponse(status_code=200, content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
