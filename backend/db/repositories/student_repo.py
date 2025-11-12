# backend/db/student_repository.py
from backend.db.database import get_connection

# NOTE: table name is `student` in DB schema (StudentID, StudentCode, FullName, ...).

class StudentRepository:
    """Xử lý truy vấn liên quan đến bảng student."""

    def get_student_by_id(self, student_id: int):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM student WHERE StudentID = %s"
            cursor.execute(query, (student_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"❌ Lỗi get_student_by_id: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_all_students(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM student")
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_all_students: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
