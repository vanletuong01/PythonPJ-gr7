# =========================================
# 📂 backend/api/register_face_routes.py
# Mục đích: API cho đăng ký khuôn mặt sinh viên
# Gọi capture_faces để chụp, sau đó xử lý DB và embedding
# =========================================

from fastapi import APIRouter, Form, HTTPException
from core.face_app.capture_faces import register_student_capture
import os

router = APIRouter()

@router.post("/register_face")
async def register_face(
    student_code: str = Form(...),
    full_name: str = Form(...)
):
    """
    API để đăng ký khuôn mặt sinh viên:
    1️⃣ Gọi camera để chụp ảnh khuôn mặt (ảnh thô)
    2️⃣ Sau khi chụp xong → lưu DB và sinh embedding
    """

    try:
        # 1️⃣ Bước 1: Gọi camera chụp ảnh
        temp_folder = register_student_capture(student_code, full_name)
        if not temp_folder or not os.path.exists(temp_folder):
            raise HTTPException(status_code=400, detail="Không thể chụp ảnh hoặc không có ảnh hợp lệ.")

        # 2️⃣ Bước 2: Xử lý DB + sinh embedding
        result = save_student_images(student_code, full_name, temp_folder)
        if not result:
            raise HTTPException(status_code=500, detail="Lỗi khi lưu DB hoặc sinh embedding.")

        return {"status": "success", "message": f"✅ Đăng ký khuôn mặt cho {full_name} thành công!"}

    except Exception as e:
        print(f"❌ Lỗi khi đăng ký khuôn mặt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
