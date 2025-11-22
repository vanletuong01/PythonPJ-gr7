import cv2
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import pymysql
import os
import base64

# ===== IMPORT CÁC MODULE AI =====
from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
from backend.app.ai.student_embedding import load_all_embeddings, fake_detector_instance
from backend.app.ai.face.detector import detect_faces_rgb, extract_face_region_rgb

# ===== KHỞI TẠO MODEL (Load 1 lần duy nhất khi chạy server) =====
embedder = ArcfaceEmbedder()
_known = load_all_embeddings()

def get_student_class_name(student_id):
    """
    Lấy tên lớp của sinh viên (lấy lớp đầu tiên nếu học nhiều lớp)
    """
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.ClassName 
            FROM study s 
            JOIN class c ON s.ClassID = c.ClassID 
            WHERE s.StudentID = %s 
            LIMIT 1
        """, (student_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "N/A"
    except Exception as e:
        print(f"❌ Error get_student_class_name: {e}")
        return "N/A"

def match_image_and_check_real(image_np_bgr):
    """
    Hàm nhận diện khuôn mặt (Hỗ trợ nhiều người cùng lúc)
    Output: Dictionary chứa danh sách các khuôn mặt đã nhận diện
    """
    # 1. Chuyển đổi ảnh BGR (OpenCV) sang RGB (PIL)
    rgb = cv2.cvtColor(image_np_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)

    # 2. Phát hiện tất cả khuôn mặt trong hình
    boxes, probs = detect_faces_rgb(pil)
    
    # Nếu không thấy mặt nào -> Trả về rỗng
    if boxes is None or len(boxes) == 0:
        return {'status': 'no_face', 'faces': []}

    # 3. Xử lý Database (Nếu rỗng thì load lại)
    global _known
    if _known["encodings"].size == 0:
        _known = load_all_embeddings()

    results = []

    # 4. DUYỆT QUA TỪNG KHUÔN MẶT (Loop)
    for box in boxes:
        # --- Bước A: Cắt ảnh khuôn mặt (Crop) ---
        face_rgb = extract_face_region_rgb(rgb, box)
        if face_rgb is None: 
            continue

        # --- Bước B: Tạo Vector đặc trưng (Embedding) ---
        face_pil = Image.fromarray(face_rgb)
        emb = embedder.get_embedding_from_pil(face_pil)
        
        if emb is None: 
            continue

        # --- Bước C: So sánh với Database ---
        student = {}
        best_score = 0.0
        found = False

        if _known["encodings"].size > 0:
            # Tính độ tương đồng (Cosine Similarity) với tất cả vector trong DB
            sims = cosine_similarity([emb], _known["encodings"])[0]
            best_idx = int(np.argmax(sims))
            best_score = float(sims[best_idx])
            
            # Ngưỡng nhận diện (0.50 - 0.55 là mức ổn định cho ArcFace)
            if best_score >= 0.50:
                found = True
                student = _known["meta"][best_idx].copy()  # Copy để tránh modify gốc
                
                # ⭐ THÊM THÔNG TIN LỚP HỌC
                student_id = student.get("id")
                if student_id:
                    student["class_name"] = get_student_class_name(student_id)
                else:
                    student["class_name"] = "N/A"
        
        # --- Bước D: Kiểm tra giả mạo (Liveness Check) ---
        is_real = True 

        # --- Bước E: Đóng gói kết quả ---
        results.append({
            "box": box.tolist(),        # Tọa độ [x1, y1, x2, y2] để vẽ khung
            "found": found,             # Có tìm thấy trong DB không
            "similarity": best_score,   # Độ chính xác (0.0 -> 1.0)
            "is_real": is_real,         # Có phải người thật không
            "student": student          # Thông tin sinh viên (ĐÃ CÓ class_name)
        })

    # 5. Trả về kết quả tổng
    return {
        "status": "ok",
        "faces": results  # Danh sách các khuôn mặt
    }


def save_attendance_to_db(study_id, similarity, photo_base64=None):
    """
    Lưu điểm danh vào DB
    - study_id: ID bản ghi trong bảng study
    - similarity: Độ chính xác nhận diện (0.0 -> 1.0)
    - photo_base64: Ảnh khuôn mặt dạng base64 (optional)
    """
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "python_project"),
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        
        # ⭐ KIỂM TRA ĐÃ ĐIỂM DANH CHƯA (Tránh trùng lặp)
        cursor.execute(
            "SELECT AttendanceID FROM attendance WHERE StudyID = %s AND Date = CURDATE()",
            (study_id,)
        )
        
        if cursor.fetchone():
            conn.close()
            return "Duplicate"  # Đã điểm danh rồi
        
        # ⭐ LƯU ĐIỂM DANH MỚI (Có PhotoPath)
        sql = """
            INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
            VALUES (%s, CURDATE(), CURTIME(), %s)
        """
        
        # Nếu có ảnh thì lưu base64, không thì lưu similarity làm placeholder
        photo_data = photo_base64 if photo_base64 else f"similarity_{similarity:.2f}"
        
        cursor.execute(sql, (study_id, photo_data))
        conn.commit()
        conn.close()
        
        return "Success"
        
    except pymysql.IntegrityError as e:
        print(f"❌ DB IntegrityError: {e}")
        return "Duplicate"
    except Exception as e:
        print(f"❌ ERROR save_attendance_to_db: {e}")
        return "Error"


def encode_image_to_base64(image_np_bgr):
    """
    Chuyển ảnh OpenCV (BGR) thành base64 string
    """
    try:
        _, buffer = cv2.imencode('.jpg', image_np_bgr)
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encode_image_to_base64: {e}")
        return None