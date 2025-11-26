import sys
import os
import cv2
import pickle
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ==============================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN (QUAN TRỌNG ĐỂ SỬA LỖI IMPORT)
# ==============================================================================
# File này đang ở: backend/app/ai/training/train_faces.py
current_file = Path(__file__).resolve()

# Root project là thư mục cha cấp 5 (D:\PythonPJ)
project_root = current_file.parents[4] 

# Thêm root vào sys.path để Python tìm thấy 'backend'
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import class Embedder
try:
    from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print("👉 Hãy kiểm tra lại file 'backend/app/ai/face/arcface_embedder.py'")
    sys.exit(1)

# ==============================================================================
# 2. CẤU HÌNH DATA & MODEL
# ==============================================================================
DATA_DIR = os.path.join(project_root, "backend", "app", "data", "face")
OUT_FILE = os.path.join(project_root, "backend", "app", "models", "face_encodings.pkl")

# NGƯỠNG NHẬN DIỆN (Dựa trên kết quả Test 0.901 của bạn)
RECOMMENDED_THRESHOLD = 0.80 

def train_embeddings():
    # Khởi tạo embedder (Model ArcFace + MTCNN Align)
    try:
        embedder = ArcfaceEmbedder()
    except Exception as e:
        print(f"❌ Không thể khởi tạo Model: {e}")
        return
    
    names = []
    encs = []
    meta = []

    print("\n" + "="*50)
    print("🚀 BẮT ĐẦU TRAINING DỮ LIỆU (CÓ ALIGNMENT)")
    print(f"📂 Data Folder: {DATA_DIR}")
    print(f"🎯 Threshold sẽ lưu: {RECOMMENDED_THRESHOLD}")
    print("="*50 + "\n")

    # Kiểm tra thư mục data
    if not os.path.exists(DATA_DIR):
        print(f"❌ Không tìm thấy thư mục: {DATA_DIR}")
        return

    folders = sorted(os.listdir(DATA_DIR))
    if not folders:
        print("❌ Thư mục data rỗng!")
        return

    for folder in tqdm(folders, desc="Processing Users"):
        path = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(path):
            continue

        person_embs = []
        
        # Lấy tất cả ảnh
        image_files = [f for f in os.listdir(path) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
        
        for f in image_files:
            img_path = os.path.join(path, f)
            img = cv2.imread(img_path)
            if img is None: continue

            # Sử dụng hàm embed_image: Tự động Detect -> Align -> Embed
            try:
                emb = embedder.embed_image(img)
                if emb is not None:
                    person_embs.append(emb)
            except Exception:
                pass

        if not person_embs:
            # print(f"⚠️ [SKIP] {folder}: Không tìm thấy mặt hợp lệ.")
            continue

        # --- LỌC NHIỄU (FILTERING) ---
        person_embs_np = np.vstack(person_embs)
        
        # Nếu có nhiều ảnh, loại bỏ các vector quá khác biệt
        if len(person_embs) > 2:
            mean_temp = np.mean(person_embs_np, axis=0)
            mean_temp /= np.linalg.norm(mean_temp)
            
            # Tính độ giống nhau với trung bình
            sims = np.dot(person_embs_np, mean_temp)
            
            # GIỮ LẠI ẢNH CÓ ĐỘ TƯƠNG ĐỒNG > 0.70 (Vì dữ liệu bạn rất tốt)
            keep_idx = np.where(sims > 0.70)[0] 
            
            if len(keep_idx) > 0:
                person_embs_np = person_embs_np[keep_idx]
            else:
                # Nếu lọc gắt quá mà mất hết thì giữ lại cái tốt nhất
                best_idx = np.argmax(sims)
                person_embs_np = person_embs_np[[best_idx]]

        # Tính trung bình cuối cùng
        mean_emb = np.mean(person_embs_np, axis=0)
        mean_emb /= np.linalg.norm(mean_emb) + 1e-9

        encs.append(mean_emb.astype(np.float32))
        names.append(folder) # Lưu tên folder (thường là MSSV)
        meta.append({"num_images": len(person_embs_np)})

    if not names:
        print("❌ Không tạo được dữ liệu nào.")
        return

    # Lưu thêm threshold vào file model
    db = {
        "encodings": np.vstack(encs).astype(np.float32),
        "names": names,
        "meta": meta,
        "threshold": RECOMMENDED_THRESHOLD # <-- Lưu ngưỡng 0.80
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "wb") as f:
        pickle.dump(db, f)

    print("\n" + "="*50)
    print(f"✅ Đã train xong {len(names)} người.")
    print(f"💾 File model đã lưu tại: {OUT_FILE}")
    print(f"⚙️  Threshold đã cấu hình: {RECOMMENDED_THRESHOLD}")
    print("="*50)

if __name__ == "__main__":
    train_embeddings()