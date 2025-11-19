from facenet_pytorch import InceptionResnetV1, MTCNN
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as transforms

class ArcfaceEmbedder:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model vggface2
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        # MTCNN để detect (chỉ dùng khi đưa ảnh nguyên gốc)
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

        # Transform chuẩn hóa ảnh đầu vào cho model
        self.transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize([0.5]*3, [0.5]*3)
        ])

    def crop_face(self, frame_bgr):
        img = Image.fromarray(frame_bgr[:, :, ::-1])  # BGR → RGB
        boxes, probs = self.mtcnn.detect(img)
        if boxes is None:
            return None
        
        # Lấy mặt to nhất
        boxes = np.array(boxes)
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        box = boxes[np.argmax(areas)]
        
        x1, y1, x2, y2 = [int(b) for b in box]
        return img.crop((x1, y1, x2, y2))

    def embed(self, face_pil):
        if face_pil is None:
            return None
        
        # Chuyển ảnh sang tensor và đưa vào model
        face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            emb = self.model(face_tensor).cpu().numpy().reshape(-1)
        
        # Chuẩn hóa vector (L2 Norm)
        norm = np.linalg.norm(emb)
        if norm == 0:
            return emb
        emb = emb.astype("float32")
        emb /= norm
        return emb

    def get_embedding(self, img_bgr):
        """Dùng khi đưa ảnh to, cần tự crop"""
        face = self.crop_face(img_bgr)
        return self.embed(face)

    def get_embedding_from_pil(self, face_pil):
        """Dùng khi đã có ảnh mặt (PIL) đã crop sẵn"""
        return self.embed(face_pil)