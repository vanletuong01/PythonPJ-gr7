"""
Auth API Routes - Controller cho đăng nhập/đăng ký giảng viên
"""
from fastapi import APIRouter, HTTPException, Form, Header
from fastapi.responses import JSONResponse
from typing import Optional

from db import Database
from services.auth_service import AuthService

# Khởi tạo router
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Khởi tạo dependencies
db = Database()
auth_service = AuthService(db)


@router.post("/login")
async def login(
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    password: str = Form(...)
):
    """
    Đăng nhập giảng viên
    - Nhập email HOẶC số điện thoại
    - Nhập mật khẩu
    """
    try:
        result = auth_service.login(email, phone, password)
        
        if result['success']:
            return JSONResponse(status_code=200, content=result)
        else:
            return JSONResponse(status_code=401, content=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):
    """Đăng ký giảng viên mới"""
    print(f"\n=== REGISTER REQUEST ===")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Phone: {phone}")
    print(f"Password length: {len(password)}")
    print("========================\n")
    
    try:
        result = auth_service.register_teacher(name, email, phone, password)
        print(f"Register result: {result}")
        
        if result['success']:
            return JSONResponse(status_code=201, content=result)
        else:
            return JSONResponse(status_code=400, content=result)
            
    except Exception as e:
        print(f"ERROR in register endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/classes/{teacher_id}")
async def get_teacher_classes(teacher_id: int):
    """Lấy danh sách lớp của giảng viên"""
    try:
        classes = auth_service.get_teacher_classes(teacher_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "total": len(classes),
                "classes": classes
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.post("/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Xác thực JWT token"""
    if not authorization:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Token không được cung cấp"}
        )
    
    try:
        # Lấy token từ header (format: "Bearer <token>")
        token = authorization.replace("Bearer ", "")
        payload = auth_service.verify_token(token)
        
        if payload:
            # Lấy thông tin teacher từ database
            teacher = db.fetch_one(
                "SELECT id_login, name, email, phone FROM login WHERE id_login = %s",
                (payload['id'],)
            )
            
            if teacher:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "teacher": {
                            "id": teacher['id_login'],
                            "name": teacher['name'],
                            "email": teacher['email'],
                            "phone": teacher['phone']
                        }
                    }
                )
        
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Token không hợp lệ hoặc hết hạn"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
