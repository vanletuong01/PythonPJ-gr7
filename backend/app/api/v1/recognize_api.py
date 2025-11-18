from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import cv2
import numpy as np

router = APIRouter()

@router.post("/ai/recognize")
async def recognize_face(file: UploadFile = File(...)):
    """API nhận diện khuôn mặt — KHÔNG lưu điểm danh"""
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

        # Gọi hàm nhận diện thông minh
        from backend.app.ai.smart_face_attendance import match_image_and_check_real

        result = match_image_and_check_real(img)

        # Trả y nguyên kết quả để test
        return JSONResponse(
            status_code=200,
            content=result
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Lỗi server: {str(e)}"
            }
        )
