# backend/app/services/capture_service.py

from pathlib import Path
import numpy as np
import cv2
from sqlalchemy.orm import Session
from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
from backend.app.crud.capture_crud import save_best_embedding
import logging

logger = logging.getLogger(__name__)

# Singleton embedder
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = ArcfaceEmbedder()
        logger.info(f"✅ ArcfaceEmbedder khởi tạo trên {_embedder.device}")
    return _embedder

def calculate_quality_score(img_bgr: np.ndarray) -> float:
    """
    Đánh giá chất lượng ảnh dựa trên:
    - Độ sắc nét (Laplacian variance)
    - Độ sáng (mean brightness)
    - Kích thước face
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Sharpness (độ sắc nét)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = laplacian.var()
    
    # Brightness (ideal: 100-180)
    brightness = gray.mean()
    brightness_score = 1.0 - abs(brightness - 140) / 140
    
    # Face size (bigger = better)
    h, w = img_bgr.shape[:2]
    face_size_score = min(h * w / (160 * 160), 1.0)
    
    # Tổng hợp (trọng số)
    quality = (
        0.5 * min(sharpness / 100, 1.0) +
        0.3 * max(0, brightness_score) +
        0.2 * face_size_score
    )
    
    return float(quality)

def save_images_and_generate_embedding(
    student_id: int,
    student_code: str,
    image_folder: Path,
    db: Session
) -> dict:
    """
    1. Đọc 25 ảnh từ folder
    2. Detect face + tính quality score
    3. Chọn ảnh tốt nhất
    4. Generate embedding
    5. Lưu vào DB
    """
    
    embedder = get_embedder()
    
    # Đọc tất cả ảnh
    image_files = sorted(image_folder.glob("*.jpg"))
    if len(image_files) == 0:
        raise ValueError("Không tìm thấy ảnh trong folder")
    
    logger.info(f"🔍 Phân tích {len(image_files)} ảnh cho {student_code}...")
    
    best_img_path = None
    best_quality = -1
    best_embedding = None
    best_face_pil = None
    
    for img_path in image_files:
        try:
            # Đọc ảnh
            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                continue
            
            # Crop face bằng MTCNN
            face_pil = embedder.crop_face(img_bgr)
            
            if face_pil is None:
                logger.warning(f"⚠️ Không detect được face: {img_path.name}")
                continue
            
            # Convert PIL -> numpy để tính quality
            face_np = np.array(face_pil)
            face_bgr = cv2.cvtColor(face_np, cv2.COLOR_RGB2BGR)
            
            # Tính quality score
            quality = calculate_quality_score(face_bgr)
            
            # Generate embedding
            emb = embedder.embed(face_pil)  # Dùng method cũ
            
            logger.info(f"  {img_path.name}: quality={quality:.3f}, emb_norm={np.linalg.norm(emb):.3f}")
            
            # Lưu ảnh tốt nhất
            if quality > best_quality:
                best_quality = quality
                best_img_path = img_path
                best_embedding = emb
                best_face_pil = face_pil
                
        except Exception as e:
            logger.error(f"❌ Lỗi xử lý {img_path.name}: {e}")
            continue
    
    if best_embedding is None:
        raise ValueError("Không tạo được embedding từ bất kỳ ảnh nào")
    
    # Lưu embedding vào DB
    embedding_id = save_best_embedding(
        db=db,
        student_id=student_id,
        embedding=best_embedding,
        image_path=str(best_img_path),
        quality_score=best_quality
    )
    
    logger.info(f"🎯 Ảnh tốt nhất: {best_img_path.name} (quality={best_quality:.3f})")
    
    # Optional: Lưu ảnh face crop tốt nhất
    if best_face_pil:
        best_face_path = image_folder / "best_face.jpg"
        best_face_pil.save(best_face_path)
        logger.info(f"💾 Lưu best face: {best_face_path}")
    
    return {
        "best_image": best_img_path.name,
        "quality_score": round(best_quality, 3),
        "embedding_saved": True,
        "embedding_id": embedding_id,
        "embedding_shape": best_embedding.shape
    }

def capture_student(student_code: str, full_name: str):
    db = next(get_db())

    # 1. tạo hoặc lấy student
    student_id = create_or_get_student(db, student_code, full_name)

    # 2. chụp ảnh
    folder = capture_face_images(student_code, full_name)

    # 3. cập nhật path ảnh
    update_student_photo(db, student_code, folder)

    # 4. sinh embedding
    emb = generate_embedding(folder)

    # 5. lưu embedding
    save_embedding(student_code, emb, full_name, folder)

    return {
        "success": True,
        "message": "Đã chụp và lưu thông tin khuôn mặt",
        "folder": folder
    }
