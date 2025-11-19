from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import cv2
import numpy as np


router = APIRouter()


@router.post("/recognize")
async def recognize_attendance(
    file: UploadFile = File(...),
    study_id: int = Form(...)
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
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Lỗi server: {str(e)}"
            }
        )