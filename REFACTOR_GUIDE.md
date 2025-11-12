"""
REFACTOR GUIDE - Hướng dẫn sử dụng các Repository và Service
(Để tránh lặp code, xử lý cursor/SQL đúng cách)

================================================================================
📋 VẤN ĐỀ TRƯỚC REFACTOR
================================================================================

1. SQL queries & cursor operations lặp lại ở nhiều file:
   - check_fake.py, smart_face_attendance.py, load_embeddings.py
   - Mỗi file đều có: conn = get_connection(), cursor.execute(...), cursor.close()
   - Không có try-finally đảm bảo đóng connection

2. Logic embedding (sinh, load, so khớp) được code lại:
   - extract_face_embedding() xuất hiện 3 chỗ
   - load_embeddings_from_mysql() xuất hiện 2 chỗ
   - Cosine similarity + normalization repeated

3. Hàm ghi điểm danh lặp ở check_fake.py & smart_face_attendance.py

================================================================================
✅ GIẢI PHÁP REFACTOR
================================================================================

Tách code thành 2 layer:
1. REPOSITORY LAYER (db/repositories.py):
   - StudentRepository: CRUD sinh viên
   - EmbeddingRepository: CRUD embeddings
   - AttendanceRepository: CRUD điểm danh
   - Tất cả SQL queries, cursor operations, try-finally đều ở đây

2. SERVICE LAYER (services/embedding_service.py):
   - EmbeddingService: Xử lý logic embedding (sinh, load, so khớp)
   - Tất cả xử lý numpy, normalization, cosine similarity

================================================================================
📌 CÁCH SỬ DỤNG - TRƯỚC & SAU
================================================================================

--- TRƯỚC (BAD - Lặp code, cursor không đóng) ---

# check_fake.py
def mark_attendance(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT StudyID FROM study WHERE StudentID = %s LIMIT 1", (student_id,))
    result = cur.fetchone()
    # ... cursor không đóng trong try-finally

# smart_face_attendance.py
def load_faces_from_mysql():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT se.StudentID, se.Embedding, ...
    # ... SQL query lặp lại

---AFTER (GOOD - Dùng repository + service) ---

# check_fake.py
from services.embedding_service import EmbeddingService
from db.repositories import AttendanceRepository

def mark_attendance(student_id):
    study_id = AttendanceRepository.get_study_id_by_student_id(student_id)
    if study_id:
        AttendanceRepository.insert_attendance(
            study_id=study_id,
            date='CURDATE()',
            time='CURTIME()',
            photo_path='photos/...'
        )

# smart_face_attendance.py
from services.embedding_service import EmbeddingService

def load_known_embeddings():
    embeddings, metadata = EmbeddingService.load_all_known_embeddings()
    return embeddings, metadata

def find_student(query_embedding):
    embeddings, metadata = EmbeddingService.load_all_known_embeddings()
    best_match, score = EmbeddingService.find_best_match(
        query_embedding, embeddings, metadata
    )
    return best_match, score

================================================================================
🔧 CÁC FILE CẦN CẬP NHẬT
================================================================================

1. check_fake.py
   Thay: conn + cursor + execute
   Bằng: AttendanceRepository.get_study_id_by_student_id()
         AttendanceRepository.insert_attendance()

2. smart_face_attendance.py
   Thay: load_faces_from_mysql() (lặp SQL)
   Bằng: EmbeddingService.load_all_known_embeddings()
   
   Thay: get_embedding() + manual normalize
   Bằng: EmbeddingService.extract_embedding_from_image()

   Thay: cosine_similarity(...) + argmax
   Bằng: EmbeddingService.find_best_match()

3. load_embeddings.py
   Thay: load_embeddings_from_mysql()
   Bằng: EmbeddingService.load_all_known_embeddings()
   
   Thay: extract_face_embedding()
   Bằng: EmbeddingService.extract_embedding_from_image()

4. face_routes.py (/api/face/register, /api/face/finalize)
   Thay: insert_embedding() (cursor trực tiếp)
   Bằng: EmbeddingRepository.insert_or_update_embedding()
   
   Thay: load_embeddings_from_mysql()
   Bằng: EmbeddingService.load_all_known_embeddings()

5. capture_faces.py (backend/capture/)
   Thay: cursor + insert/update student
   Bằng: StudentRepository.create_student() / get_student_by_code()
         StudentRepository.update_student_photo_status()
   
   Thay: insert_embedding() + DeepFace represent
   Bằng: EmbeddingService.extract_embeddings_from_folder() +
         EmbeddingService.compute_average_embedding() +
         EmbeddingRepository.insert_or_update_embedding()

================================================================================
📝 CHIA SẺ CODE - TRƯỚC & SAU EXAMPLES
================================================================================

### EXAMPLE 1: Ghi embedding (dùng ở capture_faces.py & face_routes.py)

TRƯỚC (lặp code, cursor không quản lý):
--------
# file1: capture_faces.py
def register_student_capture():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT StudentID FROM student WHERE StudentCode = %s", (student_code,))
        result = cur.fetchone()
        # ... xử lý
        # !!! Cursor không close nếu exception
        cur.close()
        conn.close()

# file2: face_routes.py endpoint
def insert_embedding(student_code, embedding, ...):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # ... tương tự code trên, lặp lại

SAU (Dùng repository):
--------
from db.repositories import StudentRepository, EmbeddingRepository
from services.embedding_service import EmbeddingService

def register_student_capture(student_code, full_name, folder_path):
    # 1. Lấy/tạo sinh viên
    student = StudentRepository.get_student_by_code(student_code)
    if not student:
        StudentRepository.create_student(full_name, student_code)
    
    # 2. Sinh embeddings từ folder
    embeddings = EmbeddingService.extract_embeddings_from_folder(folder_path)
    if embeddings:
        avg_emb = EmbeddingService.compute_average_embedding(embeddings)
        
        # 3. Lưu vào DB (cursor/conn tự động quản lý)
        EmbeddingRepository.insert_or_update_embedding(
            student_code=student_code,
            embedding=avg_emb,
            full_name=full_name,
            photo_path=folder_path
        )
        print("✅ Lưu embedding thành công")

### EXAMPLE 2: Điểm danh (dùng ở check_fake.py & smart_face_attendance.py)

TRƯỚC:
--------
# check_fake.py
def mark_attendance(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT StudyID FROM study WHERE StudentID = %s", (student_id,))
    result = cur.fetchone()
    # ... xử lý, cursor không đóng trong try-finally
    cur.close()
    conn.close()

# smart_face_attendance.py
def save_attendance_to_db(student_id, ...):
    # ... tương tự code trên

SAU (Dùng repository):
--------
from db.repositories import AttendanceRepository

def mark_attendance(student_id, photo_path):
    study_id = AttendanceRepository.get_study_id_by_student_id(student_id)
    if study_id:
        success = AttendanceRepository.insert_attendance(
            study_id=study_id,
            date='CURDATE()',
            time='CURTIME()',
            photo_path=photo_path
        )
        if success:
            print(f"✅ Điểm danh thành công cho {student_id}")
        else:
            print(f"❌ Lỗi ghi điểm danh")

### EXAMPLE 3: Load embeddings & nhận diện (dùng ở smart_face_attendance.py & check_fake.py)

TRƯỚC (SQL lặp, không quản lý cursor):
--------
# smart_face_attendance.py
def load_faces_from_mysql():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT se.StudentID, se.Embedding, ... FROM student_embeddings se ...")
    rows = cur.fetchall()
    # ... process rows
    # !!! Cursor không close trong try-finally

# check_fake.py
# ... similar code

# recognize_face()
def recognize_face(frame, known_faces):
    # ... tính embedding
    sims = cosine_similarity([emb], known_faces['encodings'])[0]
    best_idx = np.argmax(sims)
    # ... manual normalization

SAU (Dùng service + repository):
--------
from services.embedding_service import EmbeddingService

def recognize_student(frame):
    # 1. Tính embedding từ frame
    face_crop = extract_face_region(frame)
    query_emb = EmbeddingService.extract_embedding_from_image(temp_path)
    
    # 2. Load tất cả embeddings từ DB (cursor/conn tự động quản lý)
    known_embeddings, metadata = EmbeddingService.load_all_known_embeddings()
    
    # 3. Tìm best match (cosine similarity + normalization tự động)
    best_match, score = EmbeddingService.find_best_match(
        query_emb, known_embeddings, metadata, threshold=0.45
    )
    
    if best_match:
        print(f"✅ Nhận diện: {best_match['FullName']} (score={score:.3f})")
        return best_match
    else:
        print(f"❌ Không nhận diện được")
        return None

================================================================================
📂 CẤU TRÚC SAU REFACTOR
================================================================================

backend/
├── db/
│   ├── database.py (giữ nguyên: class Database + get_connection)
│   ├── config.py
│   └── repositories.py (MỚI - StudentRepository, EmbeddingRepository, AttendanceRepository)
├── services/
│   ├── embedding_service.py (MỚI - EmbeddingService)
│   ├── attendance_service.py (CẬP NHẬT - dùng Repository thay SQL trực tiếp)
│   └── auth_service.py
├── core/
│   └── face_app/
│       ├── check_fake.py (CẬP NHẬT - dùng AttendanceRepository)
│       ├── smart_face_attendance.py (CẬP NHẬT - dùng EmbeddingService)
│       └── load_embeddings.py (CẬP NHẬT - dùng EmbeddingService)
└── api/
    └── face_routes.py (CẬP NHẬT - dùng EmbeddingRepository + EmbeddingService)

================================================================================
⚙️ LỢI ÍCH CỦA REFACTOR
================================================================================

✅ DRY (Don't Repeat Yourself):
   - SQL queries viết 1 lần trong Repository
   - Logic embedding viết 1 lần trong Service
   - Tái sử dụng ở nhiều file

✅ Dễ bảo trì:
   - Thay đổi SQL? Chỉ cập nhật Repository
   - Thay đổi algorithm embedding? Chỉ cập nhật Service
   - Không cần sửa nhiều file

✅ Quản lý connection tốt:
   - try-finally ở Repository đảm bảo conn.close()
   - Tránh connection leak

✅ Khép chặt (Encapsulation):
   - Business logic không thấy SQL queries
   - API chỉ gọi service method, không cần biết chi tiết DB

✅ Dễ test:
   - Mock Repository / Service trong unit tests
   - Không cần setup DB thực

================================================================================
🚀 BƯỚC TỰA TIẾP (OPTIONAL - Nâng cao)
================================================================================

1. Thêm caching (ví dụ cache embeddings trong memory):
   - Tránh query DB mỗi lần nhận diện
   - EmbeddingService.load_all_known_embeddings() -> @cache hoặc @lru_cache

2. Async database:
   - Dùng asyncpg (PostgreSQL) hoặc aiomysql (MySQL)
   - Tránh blocking trong API endpoints

3. Migration:
   - Dùng Alembic để quản lý schema changes

================================================================================
"""
