from backend.app.models.student import Student
from backend.app.models.study import Study

def create_student(db, data):
    # 1. Kiểm tra đã tồn tại chưa
    existing = db.query(Student).filter(Student.StudentCode == data.StudentCode).first()
    
    if existing:
        # Nếu student tồn tại → chỉ lưu study
        study = Study(StudentID=existing.StudentID, ClassID=data.ClassID)
        db.add(study)
        db.commit()
        return {"success": True, "message": "Đã liên kết sinh viên với lớp"}
    
    # 2. Nếu chưa có → tạo mới trong bảng student
    new_stu = Student(
        FullName=data.FullName,
        StudentCode=data.StudentCode,
        DefaultClass=data.DefaultClass,
        Phone=data.Phone,
        AcademicYear=data.AcademicYear,
        DateOfBirth=data.DateOfBirth,
        CitizenID=data.CitizenID,
        PhotoStatus=data.PhotoStatus,
        StudentPhoto=data.StudentPhoto,
        MajorID=data.MajorID,
        TypeID=data.TypeID
    )
    db.add(new_stu)
    db.commit()
    db.refresh(new_stu)

    # 3. Tạo luôn study
    study = Study(StudentID=new_stu.StudentID, ClassID=data.ClassID)
    db.add(study)
    db.commit()

    return {"success": True, "message": "Thêm sinh viên thành công"}
