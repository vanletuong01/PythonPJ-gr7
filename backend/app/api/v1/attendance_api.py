from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import pymysql
import traceback
from datetime import datetime, date
from typing import List

# Import Models
from backend.app.models.student import Student
from backend.app.models.study import Study
from backend.app.models.attendance import Attendance
from backend.app.database import get_db

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

router = APIRouter()

# ==========================================
# 1. MODEL DỮ LIỆU (Pydantic)
# ==========================================
class ManualCheckinRequest(BaseModel):
    study_id: int
    session_date: str

# Helper function (giữ nguyên logic cũ của bạn)
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

# ==========================================
# 2. API ĐIỂM DANH THỦ CÔNG
# ==========================================
@router.post("/manual-checkin")
def manual_checkin(
    payload: ManualCheckinRequest,
    db: Session = Depends(get_db)
):
    """
    Điểm danh thủ công:
    - Nhận vào study_id và session_date.
    - Lưu Time là giờ hiện tại (để tránh lỗi NULL trong DB).
    """
    try:
        print(f"DEBUG: Nhận yêu cầu điểm danh thủ công: {payload}")
        
        # 1. Chuyển đổi ngày
        try:
            date_obj = datetime.strptime(payload.session_date, "%Y-%m-%d").date()
        except Exception as e:
            print(f"ERROR: Lỗi format ngày: {e}")
            raise HTTPException(status_code=400, detail="Ngày không hợp lệ (format: YYYY-MM-DD)")
        
        # 2. Kiểm tra đã tồn tại chưa
        existing = db.query(Attendance).filter(
            Attendance.StudyID == payload.study_id,
            Attendance.Date == date_obj
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": "Sinh viên đã được điểm danh rồi"
            }
        
        # 3. Tạo bản ghi mới
        # QUAN TRỌNG: Time lấy giờ hiện tại, PhotoPath để rỗng
        new_attendance = Attendance(
            StudyID=payload.study_id,
            Date=date_obj,
            Time=datetime.now().time(), 
            PhotoPath=""                 
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
        print("❌ LỖI DATABASE:", traceback.format_exc())
        return {
            "success": False,
            "message": f"Lỗi Server: {str(e)}"
        }

# ==========================================
# 3. API NHẬN DIỆN KHUÔN MẶT
# ==========================================
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
            return JSONResponse(status_code=400, content={"status": "error", "message": "Không đọc được ảnh"})
        
        # Gọi smart_face_attendance
        from backend.app.ai.smart_face_attendance import match_image_and_check_real, save_attendance_to_db
        
        result = match_image_and_check_real(img)
        print("DEBUG result:", result)
        
        if result.get('status') != 'ok':
            return JSONResponse(status_code=400, content=result)
        
        if not result.get('found'):
            return JSONResponse(status_code=404, content={"status": "not_found", "message": "Không khớp với sinh viên nào"})
        
        if not result.get('is_real'):
            return JSONResponse(status_code=403, content={"status": "fake", "message": "Ảnh nghi ngờ giả mạo", "real_conf": result.get('real_conf')})
        
        # Lưu điểm danh
        student = result.get('student', {})
        student_id = student.get('id')
        
        study_id = get_study_id(student_id, class_id)
        if not study_id:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Sinh viên chưa thuộc lớp này!"})
        
        save_attendance_to_db(study_id, result.get('similarity'))
        
        return {
            "status": "ok",
            "student": student,
            "similarity": result.get('similarity'),
            "real_conf": result.get('real_conf'),
            "message": "✅ Điểm danh thành công"
        }
        
    except Exception as e:
        print("ERROR in recognize_attendance:", str(e))
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Lỗi server: {str(e)}"})

# ==========================================
# 4. API LẤY CHI TIẾT BUỔI HỌC (Cho trang Session Detail)
# ==========================================
@router.get("/session-detail/{class_id}/{session_date}")
def get_session_detail(class_id: int, session_date: str, db: Session = Depends(get_db)):
    """
    Lấy danh sách SV đã điểm danh và chưa điểm danh trong một ngày cụ thể
    """
    try:
        session_date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
    except:
        raise HTTPException(status_code=400, detail="Ngày không hợp lệ (format: YYYY-MM-DD)")
    
    # Query danh sách sinh viên và join với bảng Attendance
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

# ==========================================
# 5. API LẤY LỊCH SỬ ĐIỂM DANH CÁ NHÂN (Cho trang Student Detail)
# ==========================================
@router.get("/history/{class_id}/{student_id}")
def get_student_history(class_id: int, student_id: int, db: Session = Depends(get_db)):
    """
    Lấy lịch sử điểm danh đầy đủ (Có mặt + Vắng) của 1 sinh viên
    """
    try:
        # 1. Lấy StudyID
        study_entry = db.query(Study).filter(
            Study.ClassID == class_id,
            Study.StudentID == student_id
        ).first()
        
        if not study_entry:
            return []

        target_study_id = study_entry.StudyID

        # 2. Lấy danh sách TẤT CẢ các ngày đã điểm danh của lớp này
        # (Tìm những ngày mà lớp có ít nhất 1 bản ghi điểm danh)
        class_dates = (
            db.query(Attendance.Date)
            .join(Study, Study.StudyID == Attendance.StudyID)
            .filter(Study.ClassID == class_id)
            .distinct()
            .order_by(Attendance.Date)
            .all()
        )
        
        # 3. Lấy dữ liệu điểm danh của riêng sinh viên này
        student_attendance = db.query(Attendance).filter(
            Attendance.StudyID == target_study_id
        ).all()
        
        # Map: Date -> Attendance Record
        attended_map = {att.Date: att for att in student_attendance}
        
        # 4. Tổng hợp
        history = []
        for idx, row in enumerate(class_dates, start=1):
            session_date = row.Date
            att_record = attended_map.get(session_date)
            
            is_present = att_record is not None
            
            # Xử lý hiển thị giờ
            time_str = "--:--"
            if is_present:
                # Nếu có giờ thì hiện giờ, nếu không (check tay cũ) thì hiện 'Thủ công'
                if att_record.Time:
                    time_str = att_record.Time.strftime("%H:%M:%S")
                else:
                    time_str = "Thủ công"

            history.append({
                "SessionNumber": idx,                  
                "Date": session_date.strftime("%d/%m/%Y"),
                "IsPresent": is_present,
                "Time": time_str
            })
            
        # Trả về danh sách (Mới nhất lên đầu)
        return history[::-1]

    except Exception as e:
        print(f"Error history: {e}")
        return []


# ... (Giữ nguyên các import cũ) ...

@router.get("/export/{class_id}")
def export_class_attendance(class_id: int, db: Session = Depends(get_db)):
    """
    API lấy dữ liệu để xuất Excel:
    Lấy danh sách tất cả sinh viên + thời gian điểm danh (nếu có) theo từng ngày.
    """
    try:
        # 1. Lấy danh sách tất cả các buổi học của lớp
        dates = (
            db.query(Attendance.Date)
            .join(Study, Study.StudyID == Attendance.StudyID)
            .filter(Study.ClassID == class_id)
            .distinct()
            .order_by(Attendance.Date)
            .all()
        )
        
        # 2. Lấy danh sách sinh viên
        students = (
            db.query(Student.StudentCode, Student.FullName, Study.StudyID)
            .join(Study, Study.StudentID == Student.StudentID)
            .filter(Study.ClassID == class_id)
            .all()
        )

        export_data = []

        # 3. Duyệt qua từng ngày và từng sinh viên để lấy trạng thái
        for d_row in dates:
            checkin_date = d_row.Date
            
            # Lấy các bản ghi điểm danh của ngày hôm đó
            attendance_records = db.query(Attendance).filter(
                Attendance.Date == checkin_date,
                Attendance.StudyID.in_([s.StudyID for s in students])
            ).all()
            
            # Map StudyID -> Record
            att_map = {att.StudyID: att for att in attendance_records}

            for stu in students:
                record = att_map.get(stu.StudyID)
                
                time_str = ""
                status = "Vắng"
                
                if record:
                    status = "Có mặt"
                    if record.Time:
                        time_str = record.Time.strftime("%H:%M:%S")
                    else:
                        time_str = "Thủ công"

                export_data.append({
                    "MSSV": stu.StudentCode,
                    "Họ Tên": stu.FullName,
                    "Ngày": checkin_date.strftime("%d/%m/%Y"),
                    "Giờ": time_str,
                    "Trạng thái": status
                })
                
        return export_data

    except Exception as e:
        print(f"Export Error: {e}")
        return []