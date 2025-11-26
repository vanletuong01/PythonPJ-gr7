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
        
        # MTCNN để detect và lấy landmarks
        self.mtcnn = MTCNN(
            image_size=160, 
            margin=0, 
            keep_all=True, 
            device=self.device,
            post_process=False
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
            x1, y1, x2, y2 = [int(b) for b in box]
            crop = img_np[max(0,y1):y2, max(0,x1):x2]
            return cv2.resize(crop, (160, 160))

        left_eye = landmarks[0]
        right_eye = landmarks[1]

        eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
        
        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dy, dx))

        desired_dist = 0.4 * 160
        dist = np.sqrt(dx**2 + dy**2)
        scale = desired_dist / dist if dist > 0 else 1.0

        M = cv2.getRotationMatrix2D(eye_center, angle, scale)

        tX = 160 * 0.5
        tY = 160 * 0.4 
        M[0, 2] += (tX - eye_center[0])
        M[1, 2] += (tY - eye_center[1])

        aligned_face = cv2.warpAffine(img_np, M, (160, 160), flags=cv2.INTER_CUBIC)
        return aligned_face

    def get_face_image(self, img_input):
        """
        Input: PIL Image hoặc Numpy Array (BGR)
        Output: Ảnh mặt đã crop và align (PIL Image 160x160) hoặc None
        """
        if isinstance(img_input, np.ndarray):
            img_pil = Image.fromarray(cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB))
            img_np_bgr = img_input 
        else:
            img_pil = img_input
            img_np_bgr = cv2.cvtColor(np.array(img_input), cv2.COLOR_RGB2BGR)

        boxes, probs, landmarks = self.mtcnn.detect(img_pil, landmarks=True)
        
        if boxes is None:
            return None

        areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
        idx = np.argmax(areas)
        
        box = boxes[idx]
        lm = landmarks[idx] if landmarks is not None else None
        
        aligned_bgr = self.align_face(img_np_bgr, box, lm)
        
        return Image.fromarray(cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB))

    # --- ĐÃ SỬA: Đổi tên từ embed -> get_embedding_from_pil ---
    def get_embedding_from_pil(self, face_pil):
        """
        Input: Ảnh mặt đã crop/align (PIL Image)
        Output: Vector embedding (numpy array)
        """
        if face_pil is None:
            return None
            
        if face_pil.size != (160, 160):
            face_pil = face_pil.resize((160, 160))

        face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            emb = self.model(face_tensor).cpu().numpy().reshape(-1)
        
        norm = np.linalg.norm(emb)
        if norm == 0:
            return emb
        return emb / norm

    def embed_image(self, full_image):
        """Dùng hàm này nếu bạn đưa ảnh gốc (chưa crop)"""
        face_processed = self.get_face_image(full_image)
        if face_processed is None:
            return None
        # Đã cập nhật dòng này gọi hàm mới
        return self.get_embedding_from_pil(face_processed)