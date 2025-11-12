"""
REFACTOR SUMMARY - smart_face_attendance.py
Chuyển từ Cursor trực tiếp sang Repository Pattern
"""

# ============================================================================
# ĐÃ THAY ĐỔI GÌ?
# ============================================================================

## TRƯỚC (❌ Cursor Trực Tiếp)

### 1. Imports
```python
# ❌ OLD
from backend.db.database import get_connection

def load_faces_from_mysql():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT ...")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # ... xử lý data
```

### 2. Save Attendance
```python
# ❌ OLD
def save_attendance_to_db(student_id, study_id, similarity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ...")
    cur.execute("INSERT INTO attendance ...")
    conn.commit()
    cur.close()
    conn.close()
```

---

## SAU (✅ Repository Pattern)

### 1. Imports
```python
# ✅ NEW
from backend.db.repositories import EmbeddingRepository, AttendanceRepository
from backend.core.logger import get_logger

logger = get_logger(__name__)
```

### 2. Load Embeddings
```python
# ✅ NEW
def load_faces_from_mysql():
    try:
        logger.info("Loading embeddings from database...")
        
        # Dùng Repository - không cursor trực tiếp
        embedding_repo = EmbeddingRepository()
        embeddings, meta = embedding_repo.get_all_embeddings()
        
        if embeddings.size == 0:
            logger.warning("No valid embeddings found")
            return {...}
        
        names = [str(m["StudentID"]) for m in meta]
        logger.info(f"Loaded {len(names)} embeddings")
        return {"names": names, "encodings": embeddings, "meta": meta}
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {...}
```

### 3. Save Attendance
```python
# ✅ NEW
def save_attendance_to_db(student_id, study_id, similarity):
    try:
        logger.info(f"Recording attendance for StudentID={student_id}")
        
        # Dùng Repository - không cursor trực tiếp
        attendance_repo = AttendanceRepository()
        
        # Kiểm tra xem đã điểm danh chưa
        already_attended = attendance_repo.check_already_attended_today(student_id)
        
        if already_attended:
            logger.warning(f"Student {student_id} already attended")
            return False
        
        # Ghi điểm danh
        success = attendance_repo.insert_attendance(
            student_id=student_id,
            study_id=study_id,
            distance=1.0 - similarity,
            embedding_used=True
        )
        
        if success:
            logger.info(f"✅ Attendance recorded for StudentID={student_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return False
```

---

# ============================================================================
# LỢI ỊCH CỦA REFACTOR
# ============================================================================

## ✅ LỢI ỊCH

1. **Không Trực Tiếp Cursor**
   - ❌ OLD: `conn = get_connection()`, `cur.execute()`
   - ✅ NEW: `embedding_repo.get_all_embeddings()`

2. **Quản Lý Connection Tự Động**
   - ❌ OLD: Phải tự đóng `cur.close()`, `conn.close()`
   - ✅ NEW: Repository tự xử lý try-finally

3. **Code Dễ Đọc & Bảo Trì**
   - ❌ OLD: SQL queries lẫn lộn trong business logic
   - ✅ NEW: Rõ ràng - gọi method repository, không cần biết SQL

4. **Structured Logging**
   - ❌ OLD: `print("...")`
   - ✅ NEW: `logger.info(...)`, `logger.error(..., exc_info=True)`

5. **Error Handling Tốt Hơn**
   - ❌ OLD: Exception không được tracked
   - ✅ NEW: Tất cả error log với full stack trace

6. **Tái Sử Dụng Code**
   - ❌ OLD: Logic embed lẫn trong nhiều file
   - ✅ NEW: Dùng EmbeddingRepository ở bất kỳ đâu

---

# ============================================================================
# REPOSITORY METHODS ĐƯỢC DÙNG
# ============================================================================

## 1. EmbeddingRepository
```python
# Method được dùng trong load_faces_from_mysql()
embedding_repo.get_all_embeddings() -> Tuple[np.ndarray, List[Dict]]
# Trả về: (embeddings array, list of metadata)
# Metadata bao gồm: StudentID, FullName, StudentCode
```

## 2. AttendanceRepository
```python
# Methods được dùng trong save_attendance_to_db()
attendance_repo.check_already_attended_today(student_id: int) -> bool
# Kiểm tra sinh viên đã điểm danh hôm nay chưa

attendance_repo.insert_attendance(
    student_id: int,
    study_id: int,
    distance: float,
    embedding_used: bool
) -> bool
# Ghi bản ghi điểm danh mới
```

---

# ============================================================================
# HOW IT WORKS NOW
# ============================================================================

## Flow Cũ (Old)
```
smart_face_attendance.py
    ↓
    get_connection() [return DB connection]
    ↓
    cursor.execute(SQL) [direct SQL query]
    ↓
    cursor.close(), conn.close() [manual cleanup]
    ↓
    Business Logic [xử lý data]
```

## Flow Mới (New)
```
smart_face_attendance.py
    ↓
    EmbeddingRepository() [create repo instance]
    ↓
    embedding_repo.get_all_embeddings() [call repository method]
    ↓
    [Repository handles:]
    - get_connection()
    - cursor.execute(SQL)
    - cursor.close(), conn.close()
    ↓
    Returns: (embeddings, metadata) [clean data]
    ↓
    Business Logic [xử lý data]
```

---

# ============================================================================
# TESTING
# ============================================================================

## Kiểm Tra Hoạt Động

```bash
# 1. Verify import hoạt động
python -c "from backend.core.face_app.smart_face_attendance import load_faces_from_mysql; print('✅ Import OK')"

# 2. Test load embeddings
python -c "
from backend.core.face_app.smart_face_attendance import load_faces_from_mysql
result = load_faces_from_mysql()
print(f'Loaded {len(result[\"names\"])} embeddings')
"

# 3. Run backend
python backend/main.py
```

---

# ============================================================================
# COMPARISON TABLE
# ============================================================================

| Yếu Tố | OLD (Cursor) | NEW (Repository) |
|--------|:---:|:---:|
| **Connection Management** | Manual | Automatic (try-finally) |
| **Cursor Operations** | Direct | Via Repository |
| **Error Handling** | print() | logger.error(..., exc_info=True) |
| **Code Reusability** | Scattered | Centralized |
| **Connection Leaks** | Possible | Prevented |
| **SQL Injection** | Risk | Parameterized |
| **Testability** | Hard | Easy (mock repo) |
| **Readability** | Low | High |
| **Maintenance** | Difficult | Easy |

---

# ============================================================================
# NEXT STEPS
# ============================================================================

## Files Còn Cần Refactor

- [ ] `backend/core/face_app/check_fake.py` - Nếu có cursor trực tiếp
- [ ] `backend/core/face_app/train_faces.py` - Nếu có cursor trực tiếp
- [ ] `backend/core/face_app/load_embeddings.py` - Nếu có cursor trực tiếp
- [ ] Bất kỳ file nào khác dùng `get_connection()` trực tiếp

## Kiểm Tra Nhanh

```bash
# Tìm tất cả files dùng get_connection() trực tiếp
grep -r "get_connection()" backend/ --include="*.py" | grep -v "repositories"
```

---

# ============================================================================
# SUMMARY
# ============================================================================

✅ **File `smart_face_attendance.py` đã được refactor:**
- Loại bỏ tất cả cursor operations trực tiếp
- Dùng EmbeddingRepository & AttendanceRepository
- Thêm structured logging với get_logger()
- Cải thiện error handling với exc_info=True
- Code trở nên dễ bảo trì & tái sử dụng

📌 **Lợi ích:**
- Không có connection leaks
- Dễ test (mock repository)
- Code dễ đọc
- Error tracking tốt hơn
- Reusable logic

🚀 **Tiếp theo:**
- Refactor các file face_app/ khác (nếu cần)
- Thêm tests cho smart_face_attendance.py
- Deploy & monitor
