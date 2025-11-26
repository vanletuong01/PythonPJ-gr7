# backend/app/ai/face/arcface_embedder.py

from facenet_pytorch import InceptionResnetV1, MTCNN
import torch
import numpy as np
from PIL import Image
import cv2
import torchvision.transforms as transforms

class ArcfaceEmbedder:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model FaceNet (vggface2)
        print(f"Loading FaceNet model on {self.device}...")
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        # MTCNN để detect và lấy landmarks (quan trọng)
        # image_size=160 phù hợp với InceptionResnetV1
        self.mtcnn = MTCNN(
            image_size=160, 
            margin=0, 
            keep_all=True, 
            device=self.device,
            post_process=False # Trả về raw coordinates
        )

        # Transform chuẩn hóa
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def align_face(self, img_np, box, landmarks):
        """
        Hàm thực hiện căn chỉnh (Alignment) khuôn mặt dựa trên mắt.
        """
        if landmarks is None:
            # Nếu không có landmarks, fallback về crop thường
            x1, y1, x2, y2 = [int(b) for b in box]
            crop = img_np[max(0,y1):y2, max(0,x1):x2]
            return cv2.resize(crop, (160, 160))

        # landmarks format của facenet_pytorch: [left_eye, right_eye, nose, mouth_left, mouth_right]
        left_eye = landmarks[0]
        right_eye = landmarks[1]

        # Tính toán tâm giữa 2 mắt
        eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
        
        # Tính góc nghiêng giữa 2 mắt
        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dy, dx))

        # Tính scale (để mặt không bị quá nhỏ hoặc quá to)
        # Giả sử ta muốn khoảng cách mắt chiếm khoảng 40% ảnh output 160px
        desired_dist = 0.4 * 160
        dist = np.sqrt(dx**2 + dy**2)
        scale = desired_dist / dist if dist > 0 else 1.0

        # Lấy ma trận xoay (Rotation Matrix)
        M = cv2.getRotationMatrix2D(eye_center, angle, scale)

        # Dịch chuyển tâm mắt về giữa ảnh output (80, 80)
        tX = 160 * 0.5
        tY = 160 * 0.4 # Đặt mắt hơi cao hơn giữa ảnh một chút (chuẩn face id)
        M[0, 2] += (tX - eye_center[0])
        M[1, 2] += (tY - eye_center[1])

        # Thực hiện Warp (Cắt + Xoay + Resize trong 1 bước)
        aligned_face = cv2.warpAffine(img_np, M, (160, 160), flags=cv2.INTER_CUBIC)
        return aligned_face

    def get_face_image(self, img_input):
        """
        Input: PIL Image hoặc Numpy Array (BGR)
        Output: Ảnh mặt đã crop và align (PIL Image 160x160) hoặc None
        """
        # Chuyển về PIL RGB để đưa vào MTCNN
        if isinstance(img_input, np.ndarray):
            img_pil = Image.fromarray(cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB))
            img_np_bgr = img_input # Giữ bản gốc để warp
        else:
            img_pil = img_input
            img_np_bgr = cv2.cvtColor(np.array(img_input), cv2.COLOR_RGB2BGR)

        # Detect
        boxes, probs, landmarks = self.mtcnn.detect(img_pil, landmarks=True)
        
        if boxes is None:
            return None

        # Chọn mặt to nhất (có xác suất cao nhất và diện tích lớn nhất)
        # Ở đây đơn giản lấy mặt đầu tiên (thường MTCNN sắp xếp theo độ tự tin)
        # Hoặc logic lấy diện tích lớn nhất:
        areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
        idx = np.argmax(areas)
        
        box = boxes[idx]
        lm = landmarks[idx] if landmarks is not None else None
        
        # Thực hiện ALIGNMENT
        aligned_bgr = self.align_face(img_np_bgr, box, lm)
        
        # Chuyển lại sang RGB để đưa vào model Embed
        return Image.fromarray(cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB))

    def embed(self, face_pil):
        """
        Input: Ảnh mặt đã crop/align (PIL Image)
        Output: Vector embedding (numpy array)
        """
        if face_pil is None:
            return None
            
        # Resize lại cho chắc chắn (dù align đã resize rồi)
        if face_pil.size != (160, 160):
            face_pil = face_pil.resize((160, 160))

        # Preprocess
        face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            emb = self.model(face_tensor).cpu().numpy().reshape(-1)
        
        # L2 Normalize (Bắt buộc để so sánh cosine similarity)
        norm = np.linalg.norm(emb)
        if norm == 0:
            return emb
        return emb / norm

    def embed_image(self, full_image):
        """Dùng hàm này nếu bạn đưa ảnh gốc (chưa crop)"""
        face_processed = self.get_face_image(full_image)
        if face_processed is None:
            return None
        return self.embed(face_processed)