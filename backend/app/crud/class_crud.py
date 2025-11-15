db_class = Class(
    Quantity=class_data.quantity,
    Semester=class_data.semester,
    DateStart=class_data.date_start,
    DateEnd=class_data.date_end,
    ClassName=class_data.class_name,
    FullClassName=class_data.full_class_name,
    Teacher_class=class_data.teacher_class,
    Session=class_data.session,
    CourseCode=class_data.course_code,   # ← THÊM
    TypeID=class_data.TypeID,
    MajorID=class_data.MajorID,
    ShiftID=class_data.ShiftID
)
