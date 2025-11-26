from facenet_pytorch import MTCNN
from PIL import Image
import torch
import numpy as np

# Kiểm tra xem có GPU không (nếu có sẽ nhanh hơn nhiều)
_device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"🔹 MTCNN đang chạy trên thiết bị: {_device}")

# ==========================================
# CẤU HÌNH MTCNN (TỐI ƯU CHO WEBCAM)
# ==========================================
_mtcnn = MTCNN(
    image_size=160,
    margin=0,
    min_face_size=40,   # Giảm xuống để bắt được mặt ở xa hơn (Mặc định 20)
    
    # 🔥 QUAN TRỌNG: Giảm ngưỡng nhận diện xuống
    # Mặc định là [0.6, 0.7, 0.7]. 
    # Giảm xuống [0.5, 0.6, 0.6] giúp nhận diện tốt hơn ở cam mờ/tối.
    thresholds=[0.5, 0.6, 0.6], 
    
    factor=0.709,
    post_process=True,
    keep_all=True,      # Bắt tất cả các mặt trong khung hình
    device=_device
)

def detect_faces_rgb(pil_or_np_rgb):
    """
    Hàm phát hiện khuôn mặt.
    Input: Ảnh PIL hoặc Numpy Array (RGB)
    Output: boxes (List toạ độ), probs (Độ tin cậy)
    """
    # 1. Chuẩn hóa đầu vào thành PIL Image (MTCNN thích PIL hơn Numpy)
    img_input = pil_or_np_rgb
    if not isinstance(img_input, Image.Image):
        try:
            # Nếu là numpy array, convert sang PIL
            img_input = Image.fromarray(img_input)
        except Exception as e:
            print(f"❌ Lỗi convert ảnh trong detector: {e}")
            return None, None

    try:
        # 2. Gọi model để detect
        boxes, probs = _mtcnn.detect(img_input)
        
        # --- DEBUG LOG (Xem Terminal để biết có bắt được mặt không) ---
        if boxes is not None:
            # print(f"✅ MTCNN: Tìm thấy {len(boxes)} khuôn mặt.")
            pass
        else:
            # print("⚠️ MTCNN: Không thấy mặt nào.")
            pass
            
        return boxes, probs

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng trong MTCNN: {e}")
        return None, None

def extract_face_region_rgb(rgb_frame, box):
    """
    Cắt ảnh khuôn mặt từ khung hình gốc dựa trên toạ độ box.
    box: [x1, y1, x2, y2]
    """
    try:
        if box is None: return None
        
        # Convert to int
        x1, y1, x2, y2 = [int(v) for v in box]
        h, w = rgb_frame.shape[:2]

        # Đảm bảo toạ độ không vượt quá khung hình
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # Nếu toạ độ bị lỗi (chiều rộng/cao <= 0)
        if x2 <= x1 or y2 <= y1:
            return None

        return rgb_frame[y1:y2, x1:x2]
    except Exception as e:
        print(f"❌ Lỗi cắt ảnh: {e}")
        return None