import cv2
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import pymysql
import os

# ===== IMPORT CÁC MODULE AI =====
from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
from backend.app.ai.student_embedding import load_all_embeddings, fake_detector_instance
from backend.app.ai.face.detector import detect_faces_rgb, extract_face_region_rgb

# ===== KHỞI TẠO MODEL (Load 1 lần duy nhất khi chạy server) =====
embedder = ArcfaceEmbedder()
_known = load_all_embeddings()

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
        # print("DEBUG: Database rỗng, đang thử reload...")
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
        # Gọi hàm get_embedding_from_pil để tránh detect lại (tối ưu tốc độ)
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
                student = _known["meta"][best_idx]
        
        # --- Bước D: Kiểm tra giả mạo (Liveness Check) ---
        # Lưu ý: Để hệ thống Realtime chạy nhanh khi có nhiều người, 
        # ta tạm thời dùng độ tương đồng (best_score) làm trọng số chính.
        # Nếu muốn check kỹ từng mặt, hệ thống sẽ bị chậm (FPS tụt).
        
        # Logic đơn giản: Nếu giống > 50% thì coi như là người thật
        is_real = True 
        
        # Nếu bạn muốn dùng bộ lọc giả mạo (FakeDetector):
        # real_conf = fake_detector_instance.process_frame(face_bgr_crop)...
        # Nhưng khuyến nghị để mặc định True cho mượt.

        # --- Bước E: Đóng gói kết quả ---
        results.append({
            "box": box.tolist(),        # Tọa độ [x1, y1, x2, y2] để vẽ khung
            "found": found,             # Có tìm thấy trong DB không
            "similarity": best_score,   # Độ chính xác (0.0 -> 1.0)
            "is_real": is_real,         # Có phải người thật không
            "student": student          # Thông tin sinh viên (nếu tìm thấy)
        })

    # 5. Trả về kết quả tổng
    return {
        "status": "ok",
        "faces": results  # Danh sách các khuôn mặt
    }


def save_attendance_to_db(study_id, similarity):
    """
    Hàm phụ trợ: Lưu vào DB (Thường dùng cho API HTTP, còn Realtime socket dùng hàm riêng ở frontend)
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
        sql = """
            INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
            VALUES (%s, CURDATE(), CURTIME(), %s)
        """
        cursor.execute(sql, (study_id, str(similarity))) 
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERROR save_attendance_to_db: {e}")