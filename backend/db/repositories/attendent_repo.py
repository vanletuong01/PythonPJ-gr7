# backend/db/repositories/attendent_repo.py

from typing import Optional, List, Dict
from datetime import datetime
from backend.db.database import get_connection


class AttendanceRepository:
    """
    Repository xử lý truy vấn liên quan đến bảng attendance & study.
    """

    # ==========================================================
    # 1. Lấy StudyID theo StudentID
    # ==========================================================
    def get_study_id_by_student_id(self, student_id: int) -> Optional[int]:
        """Trả về StudyID đầu tiên tương ứng với StudentID (nếu có)."""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT StudyID FROM study WHERE StudentID = %s LIMIT 1"
            cursor.execute(query, (student_id,))
            row = cursor.fetchone()
            return row["StudyID"] if row else None
        except Exception as e:
            print(f"❌ Lỗi get_study_id_by_student_id: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    # ==========================================================
    # 2. Kiểm tra StudyID đã điểm danh hôm nay chưa
    # ==========================================================
    def check_already_attended_today(self, study_id: int) -> bool:
        """
        Kiểm tra xem StudyID này đã điểm danh hôm nay chưa.
        (Dùng StudyID vì bảng attendance chỉ lưu StudyID)
        """
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT 1
                FROM attendance
                WHERE StudyID = %s
                  AND DATE(Date) = CURDATE()
                LIMIT 1
            """
            cursor.execute(query, (study_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Lỗi check_already_attended_today: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    # ==========================================================
    # 3. Ghi nhận điểm danh
    # ==========================================================
    def insert_attendance(
        self,
        study_id: int,
        photo_path: Optional[str] = None,
        date_str: Optional[str] = None,
        time_str: Optional[str] = None
    ) -> bool:
        """
        Ghi một bản ghi điểm danh mới.
        Nếu date_str/time_str = None → dùng CURDATE()/CURTIME().
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if date_str is None and time_str is None:
                query = """
                    INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                    VALUES (%s, CURDATE(), CURTIME(), %s)
                """
                cursor.execute(query, (study_id, photo_path))
            else:
                query = """
                    INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (study_id, date_str, time_str, photo_path))

            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi insert_attendance: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    # ==========================================================
    # 4. Lấy danh sách điểm danh hôm nay
    # ==========================================================
    def get_today_attendance_list(self) -> List[Dict]:
        """Trả về danh sách điểm danh hôm nay, bao gồm thông tin sinh viên."""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    a.AttendanceID,
                    a.StudyID,
                    s.StudentID,
                    st.StudentCode,
                    st.FullName,
                    a.Date,
                    a.Time,
                    a.PhotoPath
                FROM attendance a
                INNER JOIN study s ON a.StudyID = s.StudyID
                INNER JOIN student st ON s.StudentID = st.StudentID
                WHERE DATE(a.Date) = CURDATE()
                ORDER BY a.Time DESC
            """
            cursor.execute(query)
            return cursor.fetchall() or []
        except Exception as e:
            print(f"❌ Lỗi get_today_attendance_list: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
