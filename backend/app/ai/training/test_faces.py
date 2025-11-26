import os
import sys
import cv2
import random
import numpy as np
import pymysql
import pickle
from pathlib import Path

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# File này nằm ở: backend/app/ai/face/training/test_faces.py
current_file = Path(__file__).resolve()
project_root = current_file.parents[4]  # D:\PYTHONPJ
sys.path.insert(0, str(project_root))

# Import class Embedder xịn (có Alignment)
try:
    from backend.app.ai.face.arcface_embedder import ArcfaceEmbedder
except ImportError:
    print("❌ Lỗi: Không tìm thấy 'backend.app.ai.face.arcface_embedder'")
    print("👉 Hãy kiểm tra lại đường dẫn file hoặc sys.path")
    sys.exit(1)

DATA_DIR = os.path.join(project_root, "backend", "app", "data", "face")

# ===============================
# 1. HÀM LẤY VECTOR TỪ DB (TẬP CHUẨN)
# ===============================
def load_db_embeddings():
    print("📡 Đang tải vector mẫu từ Database...")
    try:
        conn = pymysql.connect(
            host="localhost", 
            user="root", 
            password="",   # <--- NHẬP PASSWORD DB NẾU CÓ
            database="python_project"
        )
        cursor = conn.cursor()
        
        # Lấy StudentCode và EmbeddingBlob
        sql = """
            SELECT s.StudentCode, e.Embedding 
            FROM student s
            JOIN student_embeddings e ON s.StudentID = e.StudentID
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        db_data = {}
        for mssv, blob in rows:
            if blob:
                # Giải mã binary thành numpy array
                emb = pickle.loads(blob)
                db_data[mssv] = emb
        
        conn.close()
        print(f"✅ Đã tải {len(db_data)} vector sinh viên từ DB.")
        return db_data
    except Exception as e:
        print(f"❌ Lỗi kết nối DB: {e}")
        return {}

# ===============================
# 2. HÀM TEST ĐỘ CHÍNH XÁC (20% ẢNH GỐC)
# ===============================
def test_accuracy_with_raw_images(test_ratio=0.2):
    # 1. Tải mốc chuẩn
    db_embeddings = load_db_embeddings()
    if not db_embeddings:
        print("⚠️ Database rỗng hoặc không kết nối được.")
        return

    # 2. Khởi tạo Embedder
    try:
        embedder = ArcfaceEmbedder()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Model: {e}")
        return
    
    print(f"\n🚀 Bắt đầu test trên {test_ratio*100}% dữ liệu ảnh gốc...")
    
    y_true = [] # Nhãn thực tế (MSSV của folder)
    y_pred = [] # Nhãn dự đoán (MSSV tìm thấy trong DB)
    scores = [] # Độ tương đồng
    
    folders = sorted(os.listdir(DATA_DIR))
    
    total_images_tested = 0
    
    for mssv_folder in folders:
        folder_path = os.path.join(DATA_DIR, mssv_folder)
        if not os.path.isdir(folder_path): continue
        
        # Nếu MSSV này không có trong DB thì bỏ qua (không thể test so sánh)
        if mssv_folder not in db_embeddings:
            continue
            
        # Lấy danh sách ảnh (Thêm đuôi jpeg cho chắc chắn)
        images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # --- SỬA LỖI QUAN TRỌNG: CHECK RỖNG ---
        if not images:
            print(f"⚠️ Cảnh báo: Thư mục {mssv_folder} không có ảnh nào. Bỏ qua.")
            continue
        
        # --- LẤY NGẪU NHIÊN 20% SỐ ẢNH ---
        # Tính toán số lượng cần lấy
        calc_size = int(len(images) * test_ratio)
        
        # Logic an toàn: Lấy ít nhất 1 ảnh, nhưng KHÔNG ĐƯỢC LỚN HƠN tổng số ảnh đang có
        sample_size = max(1, calc_size)       # Ít nhất là 1
        sample_size = min(sample_size, len(images)) # Không vượt quá tổng số
        
        test_images = random.sample(images, sample_size)
        
        for img_name in test_images:
            img_path = os.path.join(folder_path, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            
            # Tính vector của ảnh test (Có Align)
            try:
                test_emb = embedder.embed_image(img)
                if test_emb is None:
                    continue
                
                # So sánh với TOÀN BỘ DB để tìm người giống nhất
                # (Mô phỏng thực tế điểm danh)
                best_score = -1
                best_match = "Unknown"
                
                # Duyệt qua tất cả vector trong DB để tìm người giống nhất
                for db_mssv, db_emb in db_embeddings.items():
                    # Tính cosine similarity
                    score = np.dot(test_emb, db_emb)
                    if score > best_score:
                        best_score = score
                        best_match = db_mssv
                
                y_true.append(mssv_folder)
                y_pred.append(best_match)
                scores.append(best_score)
                total_images_tested += 1
                
            except Exception as e:
                print(f"Lỗi khi xử lý ảnh {img_name}: {e}")
                pass

    # ===============================
    # 3. TÍNH TOÁN KẾT QUẢ
    # ===============================
    if total_images_tested == 0:
        print("⚠️ Không kiểm tra được ảnh nào (Folder rỗng hoặc lỗi).")
        return

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    scores = np.array(scores)
    
    # Tính Accuracy với các ngưỡng (Threshold) khác nhau
    print("\n📊 KẾT QUẢ ĐÁNH GIÁ:")
    print(f"∑ Tổng số ảnh đã test: {total_images_tested}")
    print("-" * 40)
    print(f"{'THRESHOLD':<10} | {'ACCURACY':<10} | {'FALSE REJECT':<12}")
    print("-" * 40)
    
    for threshold in [0.4, 0.5, 0.6, 0.7, 0.8]:
        # Logic nhận diện:
        # Nếu Score > Threshold VÀ Pred == True -> Đúng (True Positive)
        # Nếu Score < Threshold -> Unknown (Coi như sai nếu đang test nhận diện chính chủ)
        
        # Đếm số lần nhận đúng người VÀ vượt qua ngưỡng
        correct_predictions = ((y_pred == y_true) & (scores >= threshold)).sum()
        accuracy = (correct_predictions / total_images_tested) * 100
        
        # Tỉ lệ từ chối sai (Là người thật nhưng score thấp hơn ngưỡng)
        false_reject_count = ((y_pred == y_true) & (scores < threshold)).sum()
        frr = (false_reject_count / total_images_tested) * 100
        
        print(f"{threshold:<10} | {accuracy:6.2f}%   | {frr:6.2f}%")
    
    print("-" * 40)
    
    # Gợi ý ngưỡng tốt nhất
    # Chỉ tính trung bình score của những trường hợp ĐÚNG NGƯỜI (True Positive)
    correct_cases = scores[y_pred == y_true]
    if len(correct_cases) > 0:
        avg_score_correct = np.mean(correct_cases)
        print(f"💡 Điểm tương đồng trung bình (Mean Similarity) của đúng người: {avg_score_correct:.3f}")
        print(f"👉 Nên đặt ngưỡng (Threshold) khoảng: {avg_score_correct - 0.1:.2f} - {avg_score_correct - 0.05:.2f}")
    else:
        print("⚠️ Không có trường hợp nào nhận diện đúng, cần kiểm tra lại dữ liệu.")

if __name__ == "__main__":
    test_accuracy_with_raw_images(test_ratio=0.2) # Test 20%