import os
import sys
import cv2
import pymysql
import pickle
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# --- 1. CẤU HÌNH ĐƯỜNG DẪN GỐC ---
# Lấy đường dẫn thư mục hiện tại (PYTHONPJ)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# --- 2. CẤU HÌNH ĐƯỜNG DẪN DATASET (THEO ẢNH BẠN GỬI) ---
# Trỏ vào: backend/app/data/face
DATASET_DIR = os.path.join(ROOT_DIR, "backend", "app", "data", "face")

# Load biến môi trường (.env)
load_dotenv()

# --- 3. IMPORT CLASS AI CỦA BẠN ---
try:
    from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
    print("✅ Đã load thành công module ArcfaceEmbedder!")
except ImportError as e:
    print(f"❌ Lỗi import: {e}")
    print("👉 Hãy chắc chắn bạn để file này ở thư mục gốc (PYTHONPJ)")
    sys.exit(1)

# --- 4. CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "python_project"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def main():
    # Kiểm tra thư mục data có tồn tại không
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Không tìm thấy thư mục dữ liệu tại: {DATASET_DIR}")
        print("👉 Bạn hãy kiểm tra lại xem tên folder có đúng là 'backend/app/data/face' không nhé.")
        return

    # Khởi tạo Model AI
    print("⏳ Đang khởi tạo model ArcFace (chờ chút)...")
    try:
        embedder = ArcfaceEmbedder()
        print("🚀 Model đã sẵn sàng!")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Model: {e}")
        return

    # Kết nối DB
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("🔌 Đã kết nối Database thành công.")
    except Exception as e:
        print(f"❌ Lỗi kết nối DB: {e}")
        return

    # Lấy danh sách folder (MSSV)
    folders = os.listdir(DATASET_DIR)
    print(f"📂 Tìm thấy {len(folders)} thư mục sinh viên trong {DATASET_DIR}")

    success_count = 0
    fail_count = 0

    for mssv in folders:
        folder_path = os.path.join(DATASET_DIR, mssv)
        if not os.path.isdir(folder_path):
            continue

        print(f"\n🔍 Đang xử lý SV có MSSV: {mssv}...")

        # --- QUAN TRỌNG: Tìm StudentID từ MSSV (StudentCode) ---
        cursor.execute("SELECT StudentID, FullName FROM student WHERE StudentCode = %s", (mssv,))
        student = cursor.fetchone()

        if not student:
            print(f"   ⚠️ Không tìm thấy MSSV '{mssv}' trong Database. -> Bỏ qua!")
            continue
        
        student_id = student['StudentID']
        full_name = student['FullName']
        print(f"   👤 Sinh viên: {full_name} (ID: {student_id})")

        # Duyệt ảnh trong folder
        images = os.listdir(folder_path)
        first_valid_photo = None 

        for img_name in images:
            img_path = os.path.join(folder_path, img_name)
            
            # Đọc ảnh (OpenCV đọc BGR)
            img_bgr = cv2.imread(img_path)
            
            if img_bgr is None:
                continue
            
            try:
                # Trích xuất đặc trưng (512 chiều)
                embedding = embedder.get_embedding(img_bgr)
                
                if embedding is not None:
                    # Nén vector thành binary
                    emb_blob = pickle.dumps(embedding)
                    
                    # Lưu vào DB (StudentEmbeddings)
                    sql = """
                        INSERT INTO student_embeddings 
                        (StudentID, Embedding, EmbeddingDim, PhotoPath, Quality, Source)
                        VALUES (%s, %s, %s, %s, %s, 'dataset_import')
                    """
                    cursor.execute(sql, (student_id, emb_blob, 512, img_path, 1.0))
                    conn.commit()
                    
                    print(f"   ✅ Đã import ảnh: {img_name}")
                    success_count += 1
                    
                    if first_valid_photo is None:
                        first_valid_photo = img_path
                else:
                    print(f"   ❌ Không tìm thấy mặt trong ảnh: {img_name}")
                    fail_count += 1

            except Exception as e:
                print(f"   🔥 Lỗi file {img_name}: {e}")
                fail_count += 1

        # Cập nhật Avatar cho bảng student (nếu chưa có)
        if first_valid_photo:
            # Chỉ cập nhật nếu StudentPhoto đang trống
            cursor.execute("""
                UPDATE student SET StudentPhoto = %s 
                WHERE StudentID = %s AND (StudentPhoto IS NULL OR StudentPhoto = '')
            """, (first_valid_photo, student_id))
            conn.commit()

    conn.close()
    print("\n" + "="*30)
    print(f"🎉 HOÀN TẤT QUÁ TRÌNH IMPORT!")
    print(f"✅ Thành công: {success_count} ảnh")
    print(f"❌ Thất bại: {fail_count} ảnh")

if __name__ == "__main__":
    main()