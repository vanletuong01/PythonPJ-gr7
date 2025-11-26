import sys
import os
from pathlib import Path
import cv2
import numpy as np
import pickle
import pymysql
from tqdm import tqdm

# ==============================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ==============================================================================
# File này nằm ở: backend/app/ai/face/training/import_data.py
current_file = Path(__file__).resolve()

# Root project là thư mục cha cấp 5 (PYTHONPJ)
project_root = current_file.parents[4] 

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import Class ArcfaceEmbedder mới (Đã có tính năng Alignment)
try:
    from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print("👉 Hãy kiểm tra lại đường dẫn file 'arcface_embedder.py'")
    sys.exit(1)

# Đường dẫn data ảnh: D:\PYTHONPJ\backend\app\data\face
DATA_DIR = os.path.join(project_root, "backend", "app", "data", "face")

# ==============================================================================
# 2. KẾT NỐI DATABASE
# ==============================================================================
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",     # <--- NHẬP PASSWORD DATABASE CỦA BẠN VÀO ĐÂY
        database="python_project",
        port=3306,
        charset="utf8mb4",
        autocommit=True
    )

# ==============================================================================
# 3. HÀM XỬ LÝ CHÍNH
# ==============================================================================
def import_embeddings_to_db():
    print(f"📂 Data Directory: {DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ Không tìm thấy thư mục ảnh: {DATA_DIR}")
        return

    # 1. Khởi tạo Model (Chỉ load 1 lần để tiết kiệm RAM)
    try:
        embedder = ArcfaceEmbedder() 
        print("✅ Model ArcFace đã tải thành công.")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Model: {e}")
        return

    # 2. Kết nối DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Đã kết nối Database MySQL.")
    except Exception as e:
        print(f"❌ Lỗi kết nối DB: {e}")
        return

    # 3. Lấy danh sách thư mục sinh viên
    student_folders = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])
    
    if not student_folders:
        print("⚠️ Không tìm thấy thư mục sinh viên nào.")
        return

    print(f"🚀 Bắt đầu xử lý {len(student_folders)} sinh viên...")
    success_count = 0
    
    for mssv in tqdm(student_folders, desc="Processing"):
        student_path = os.path.join(DATA_DIR, mssv)
        
        # --- BƯỚC A: LẤY StudentID TỪ MSSV ---
        cursor.execute("SELECT StudentID FROM student WHERE StudentCode = %s", (mssv,))
        row = cursor.fetchone()
        
        if not row:
            # Nếu MSSV này chưa có trong bảng student thì bỏ qua
            continue
            
        student_id = row[0]
        
        # --- BƯỚC B: ĐỌC ẢNH & TÍNH VECTOR ---
        embeddings = []
        image_files = [f for f in os.listdir(student_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        avatar_path = "" # Dùng để lưu đường dẫn ảnh đại diện
        
        for img_name in image_files:
            full_path = os.path.join(student_path, img_name)
            
            # Lưu đường dẫn ảnh đầu tiên để làm avatar (đường dẫn tương đối)
            if not avatar_path:
                # Chuyển path tuyệt đối thành tương đối để lưu DB (backend/app/data/face/SV001/...)
                try:
                    rel_path = os.path.relpath(full_path, project_root)
                    avatar_path = rel_path.replace("\\", "/") # Chuẩn hóa path cho Web
                except:
                    avatar_path = full_path

            img = cv2.imread(full_path)
            if img is None: continue

            try:
                # Dùng hàm embed_image của Class: Tự động Detect -> Align -> Embed
                emb = embedder.embed_image(img)
                if emb is not None:
                    embeddings.append(emb)
            except Exception as e:
                pass

        # --- BƯỚC C: TÍNH VECTOR TRUNG BÌNH (CÓ LỌC NHIỄU) ---
        if len(embeddings) > 0:
            final_emb = None
            
            # 1. Chuyển list sang numpy array
            emb_matrix = np.vstack(embeddings)

            # 2. Logic lọc nhiễu (loại bỏ các ảnh quá khác biệt so với số đông)
            if len(embeddings) > 2:
                # Tính trung bình tạm
                mean_temp = np.mean(emb_matrix, axis=0)
                mean_temp /= np.linalg.norm(mean_temp)
                
                # Tính độ giống nhau (Cosine Similarity) của từng ảnh với trung bình tạm
                sims = np.dot(emb_matrix, mean_temp)
                
                # Chỉ giữ lại ảnh có độ giống > 0.6
                valid_indices = np.where(sims > 0.6)[0]
                
                if len(valid_indices) > 0:
                    emb_matrix = emb_matrix[valid_indices]
                else:
                    # Nếu lọc hết sạch thì lấy cái giống nhất
                    best_idx = np.argmax(sims)
                    emb_matrix = emb_matrix[[best_idx]]
            
            # 3. Tính trung bình cuối cùng
            mean_emb = np.mean(emb_matrix, axis=0)
            
            # 4. Chuẩn hóa L2 (CỰC KỲ QUAN TRỌNG ĐỂ SO SÁNH)
            mean_emb /= np.linalg.norm(mean_emb) + 1e-9
            
            # 5. Serialize sang binary để lưu Blob
            binary_vector = pickle.dumps(mean_emb.astype(np.float32))

            # --- BƯỚC D: LƯU VÀO DATABASE ---
            try:
                # Xóa vector cũ nếu có
                cursor.execute("DELETE FROM student_embeddings WHERE StudentID = %s", (student_id,))
                
                # Insert mới
                sql = """
                    INSERT INTO student_embeddings 
                    (StudentID, Embedding, EmbeddingDim, PhotoPath, Quality, Source, CreatedAt)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, (student_id, binary_vector, 512, avatar_path, 1.0, 'dataset_import'))
                
                # Cập nhật trạng thái có ảnh cho sinh viên
                cursor.execute("UPDATE student SET PhotoStatus = 'YES' WHERE StudentID = %s", (student_id,))
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ Lỗi SQL StudentID {student_id}: {e}")
        else:
            # print(f"⚠️ StudentID {student_id}: Không trích xuất được khuôn mặt nào.")
            pass

    conn.close()

    print("\n" + "="*50)
    print(f"🎉 HOÀN TẤT IMPORT!")
    print(f"✅ Đã lưu vector chuẩn (Aligned) cho: {success_count} sinh viên.")
    print("="*50)

if __name__ == "__main__":
    import_embeddings_to_db()