"""
Authentication Service - Xử lý đăng nhập/đăng xuất giảng viên
"""
from typing import Optional
from db import Database
from datetime import datetime, timedelta
import bcrypt
import jwt
from db.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """Service xử lý authentication cho giảng viên"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """Hash password bằng bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Kiểm tra password"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except:
            # Fallback: nếu password chưa được hash (database cũ)
            return plain_password == hashed_password
    
    def create_access_token(self, data: dict) -> str:
        """Tạo JWT token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Xác thực JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login(self, email: Optional[str], phone: Optional[str], password: str) -> dict:
        """
        Đăng nhập giảng viên
        
        Args:
            email: Email giảng viên
            phone: Số điện thoại giảng viên
            password: Mật khẩu
        
        Returns:
            dict với thông tin giảng viên hoặc lỗi
        """
        try:
            # Kết nối database
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            # Tìm giảng viên theo email hoặc phone
            if email:
                teacher = self.db.fetch_one(
                    "SELECT * FROM login WHERE email = %s",
                    (email,)
                )
            elif phone:
                teacher = self.db.fetch_one(
                    "SELECT * FROM login WHERE phone = %s",
                    (phone,)
                )
            else:
                return {
                    "success": False,
                    "message": "Vui lòng nhập email hoặc số điện thoại"
                }
            
            if not teacher:
                return {
                    "success": False,
                    "message": "Tài khoản không tồn tại"
                }
            
            # Kiểm tra password với bcrypt hoặc plain text (backward compatible)
            if self.verify_password(password, teacher['pass']):
                # Tạo JWT token
                token_data = {
                    "id": teacher['id_login'],
                    "email": teacher['email'],
                    "type": "teacher"
                }
                access_token = self.create_access_token(token_data)
                
                return {
                    "success": True,
                    "message": "Đăng nhập thành công",
                    "token": access_token,
                    "teacher": {
                        "id": teacher['id_login'],
                        "name": teacher['name'],
                        "email": teacher['email'],
                        "phone": teacher['phone']
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Mật khẩu không đúng"
                }
        except Exception as e:
            print(f"ERROR in login: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }
    
    def get_teacher_classes(self, teacher_id: int) -> list:
        """Lấy danh sách lớp của giảng viên"""
        try:
            # Kết nối database
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            classes = self.db.fetch_all(
                """SELECT c.*, m.MajorName, t.TypeName, s.ShiftName
                   FROM teach tc
                   JOIN class c ON tc.ClassID = c.ClassID
                   JOIN major m ON c.MajorID = m.MajorID
                   JOIN type t ON c.TypeID = t.TypeID
                   JOIN shift s ON c.ShiftID = s.ShiftID
                   WHERE tc.id_login = %s""",
                (teacher_id,)
            )
            return classes or []
        except Exception as e:
            print(f"ERROR in get_teacher_classes: {str(e)}")
            return []
    
    def register_teacher(self, name: str, email: str, phone: str, password: str) -> dict:
        """Đăng ký giảng viên mới"""
        try:
            # Kết nối database
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            # Kiểm tra email đã tồn tại
            existing = self.db.fetch_one(
                "SELECT * FROM login WHERE email = %s OR phone = %s",
                (email, phone)
            )
            
            if existing:
                return {
                    "success": False,
                    "message": "Email hoặc số điện thoại đã được sử dụng"
                }
            
            # Hash password trước khi lưu
            hashed_password = self.hash_password(password)
            
            # Thêm giảng viên mới
            teacher_id = self.db.execute_query(
                "INSERT INTO login (name, email, phone, pass) VALUES (%s, %s, %s, %s)",
                (name, email, phone, hashed_password)
            )
            
            if teacher_id:
                return {
                    "success": True,
                    "message": "Đăng ký thành công",
                    "teacher_id": teacher_id
                }
            else:
                return {
                    "success": False,
                    "message": "Lỗi khi tạo tài khoản"
                }
        except Exception as e:
            print(f"ERROR in register_teacher: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }
