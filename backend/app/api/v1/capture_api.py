# backend/app/api/capture_api.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pathlib import Path
import base64
import shutil
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.student import Student
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ========================================
# ĐƯỜNG DẪN: backend/app/data/face/{MSSV}/
# ========================================
CURRENT_FILE = Path(__file__).resolve()
APP_DIR = CURRENT_FILE.parents[2]  # backend/app/
DATA_DIR = APP_DIR / "data" / "face"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"🔥 DATA_DIR: {DATA_DIR.absolute()}")

class CaptureUpload(BaseModel):
    student_code: str
    full_name: str
    images: list[str]

def safe_name(s: str):
    """Chuyển tên tiếng Việt thành ASCII an toàn"""
    import re, unicodedata
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^A-Za-z0-9_-]+', '_', s).strip('_')
    return s or "student"

@router.post("/save-face-images")
async def save_face_images(
    payload: CaptureUpload,
    db: Session = Depends(get_db)
):
    """
    Lưu 25 ảnh khuôn mặt sinh viên vào backend/app/data/face/{MSSV}/
    """
    logger.info("=" * 70)
    logger.info(f"📥 NHẬN REQUEST CHỤP ẢNH")
    logger.info(f"   Student Code: {payload.student_code}")
    logger.info(f"   Full Name: {payload.full_name}")
    logger.info(f"   Số ảnh: {len(payload.images)}")
    logger.info("=" * 70)
    
    # Tìm sinh viên trong DB
    stu = db.query(Student).filter(Student.StudentCode == payload.student_code).first()
    
    if not stu:
        logger.warning(f"⚠️  Sinh viên {payload.student_code} chưa tồn tại, tạo mới...")
        
        stu = Student(
            StudentCode=payload.student_code,
            FullName=payload.full_name,
            PhotoStatus="PENDING"
        )
        db.add(stu)
        db.commit()
        db.refresh(stu)
        
        logger.info(f"✅ Đã tạo sinh viên mới: ID={stu.StudentID}")
    else:
        logger.info(f"✅ Sinh viên đã tồn tại: ID={stu.StudentID}, Name={stu.FullName}")
    
    # Tạo folder: backend/app/data/face/{MSSV}/
    folder = DATA_DIR / safe_name(payload.student_code)
    logger.info(f"\n📁 Folder: {folder.absolute()}")
    
    if folder.exists():
        logger.info(f"🗑️  Xóa folder cũ...")
        shutil.rmtree(folder)
    
    folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Đã tạo folder mới")
    
    # Lưu từng ảnh
    saved_paths = []
    failed_count = 0
    
    logger.info(f"\n📸 Bắt đầu lưu {len(payload.images)} ảnh...")
    
    for idx, img_b64 in enumerate(payload.images, start=1):
        try:
            # Loại bỏ header base64 (nếu có)
            if "," in img_b64:
                img_b64 = img_b64.split(",", 1)[1]
            
            # Decode base64
            img_bytes = base64.b64decode(img_b64)
            
            if len(img_bytes) == 0:
                logger.warning(f"  [{idx:02d}] ❌ Ảnh rỗng (0 bytes)")
                failed_count += 1
                continue
            
            # Tạo tên file
            filename = f"{payload.student_code}_{idx:02d}.jpg"
            file_path = folder / filename
            
            # Ghi file
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            
            # Kiểm tra file đã lưu thành công
            if file_path.exists():
                size = file_path.stat().st_size
                logger.info(f"  [{idx:02d}] ✅ {filename} ({size:,} bytes)")
                saved_paths.append(str(file_path))
            else:
                logger.error(f"  [{idx:02d}] ❌ Không lưu được file")
                failed_count += 1
                
        except base64.binascii.Error as e:
            logger.error(f"  [{idx:02d}] ❌ Lỗi decode base64: {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"  [{idx:02d}] ❌ Lỗi: {e}")
            failed_count += 1
    
    logger.info(f"\n🎯 KẾT QUẢ:")
    logger.info(f"   Thành công: {len(saved_paths)}/25")
    logger.info(f"   Thất bại: {failed_count}/25")
    logger.info(f"   Folder: {folder.absolute()}")
    
    # Kiểm tra số lượng ảnh tối thiểu
    if len(saved_paths) < 5:
        raise HTTPException(
            status_code=400, 
            detail=f"Chỉ lưu được {len(saved_paths)}/25 ảnh. Vui lòng chụp lại!"
        )
    
    # Cập nhật database
    stu.StudentPhoto = str(folder.absolute())
    stu.PhotoStatus = "DONE"
    db.commit()
    logger.info(f"✅ Cập nhật DB: StudentPhoto={stu.StudentPhoto}")
    logger.info("=" * 70)

    # ======= THÊM ĐOẠN NÀY ĐỂ SINH VÀ LƯU EMBEDDING =========
    from backend.app.services.capture_service import save_images_and_generate_embedding
    try:
        embedding_result = save_images_and_generate_embedding(
            student_id=stu.StudentID,
            student_code=payload.student_code,
            image_folder=folder,
            db=db
        )
    except Exception as e:
        logger.error(f"Lỗi sinh embedding: {e}")
        embedding_result = {"embedding_saved": False, "error": str(e)}
    # ========================================================

    return {
        "success": True,
        "message": f"Đã lưu {len(saved_paths)} ảnh thành công",
        "folder": str(folder.absolute()),
        "student_code": payload.student_code,
        "student_id": stu.StudentID,
        "saved": len(saved_paths),
        "failed": failed_count,
        "sample_files": [
            f.name for f in sorted(folder.glob("*.jpg"))[:5]
        ],
        "embedding_result": embedding_result,  # trả về kết quả embedding
    }
