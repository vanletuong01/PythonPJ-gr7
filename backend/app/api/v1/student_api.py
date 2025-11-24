from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.models.major import Major
from backend.app.models.type import Type
from backend.app.models.study import Study
from backend.app.models.class_model import Class
from backend.app.database import get_db
from backend.app.services.student_service import search_students, create_student
from backend.app.schemas.student_schemas import StudentCreate
from backend.app.crud.student_crud import get_student_detail

router = APIRouter(tags=["Student"])

@router.get("/search")
def search_students(q: str = Query(..., min_length=1), limit: int = 30, db: Session = Depends(get_db)):
    # Tìm theo tên hoặc mã số sinh viên (StudentCode)
    results = (
        db.query(
            Student,
            Major.Full_name_mj,
            Type.TypeName
        )
        .join(Major, Student.MajorID == Major.MajorID)
        .join(Type, Student.TypeID == Type.TypeID)
        .filter(
            (Student.FullName.ilike(f"%{q}%")) |
            (Student.StudentCode.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    # Trả về dữ liệu dạng list[dict]
    return [
        {
            "StudentID": s.StudentID,
            "FullName": s.FullName,
            "StudentCode": s.StudentCode,
            "DefaultClass": getattr(s, "DefaultClass", None),
            "Phone": getattr(s, "Phone", None),
            "DateOfBirth": getattr(s, "DateOfBirth", None),
            "CitizenID": getattr(s, "CitizenID", None),
            "AcademicYear": getattr(s, "AcademicYear", None),
            "Full_name_mj": full_name_mj,
            "TypeName": type_name,
            "ClassID": getattr(s, "ClassID", None),
            "MajorID": getattr(s, "MajorID", None),
            "TypeID": getattr(s, "TypeID", None),
            "PhotoStatus": getattr(s, "PhotoStatus", None)
        }
        for s, full_name_mj, type_name in results
    ]

@router.post("/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db)):
    # Kiểm tra trùng MSSV
    existing = db.query(Student).filter(Student.StudentCode == data.StudentCode).first()
    if existing:
        return {"success": False, "detail": "MSSV đã tồn tại"}
    # Tạo mới
    student = Student(
        FullName=data.FullName,
        StudentCode=data.StudentCode,
        DefaultClass=data.DefaultClass,
        Phone=data.Phone,
        AcademicYear=data.AcademicYear,
        DateOfBirth=data.DateOfBirth,
        CitizenID=data.CitizenID,
        MajorID=data.MajorID,
        TypeID=data.TypeID,
        PhotoStatus=data.PhotoStatus,
        StudentPhoto=data.StudentPhoto
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"success": True, "student_id": student.StudentID}

@router.get("/detail/{student_id}")
def api_get_student_detail(student_id: int, db: Session = Depends(get_db)):
    student = get_student_detail(db, student_id)
    if not student:
        return {"success": False, "message": "Không tìm thấy sinh viên"}
    return {"success": True, "data": student}

@router.get("/students_in_class/{class_id}")
def get_students_in_class(class_id: int, db: Session = Depends(get_db)):
    # Lấy danh sách sinh viên thuộc lớp
    results = (
        db.query(Student.StudentID, Student.FullName, Student.StudentCode)
        .join(Study, Study.StudentID == Student.StudentID)
        .filter(Study.ClassID == class_id)
        .all()
    )
    # Trả về list[dict] có StudentID
    return [
        {
            "StudentID": s.StudentID,
            "FullName": s.FullName,
            "StudentCode": s.StudentCode
        }
        for s in results
    ]

@router.post("/update")
def update_student(data: dict, db: Session = Depends(get_db)):
    student_id = data.get("StudentID")
    db.query(Student).filter(Student.StudentID == student_id).update({
        Student.FullName: data.get("FullName"),
        Student.DefaultClass: data.get("DefaultClass"),
        Student.DateOfBirth: data.get("DateOfBirth"),
        Student.Phone: data.get("Phone"),
        Student.CitizenID: data.get("CitizenID"),
    })
    db.commit()
    return {"success": True}
