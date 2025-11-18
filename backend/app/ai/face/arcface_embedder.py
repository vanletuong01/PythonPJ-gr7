# ===============================================
# arcface_embedder.py  (BẢN TỐI ƯU – 2025)
# ===============================================
from facenet_pytorch import InceptionResnetV1, MTCNN
import torch
import numpy as np
from PIL import Image
import cv2
import torchvision.transforms as transforms


class ArcfaceEmbedder:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        # Load ArcFace InceptionResnetV1 – VGGFace2
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

        # MTCNN detect – keep_all=True để chọn mặt lớn nhất
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

        self.transform = transforms.Compose([
            transforms.Resize((160, 160), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.5]*3, [0.5]*3)
        ])

    # -------------------------------------------------------------
    # Detect mặt và crop mặt lớn nhất
    # -------------------------------------------------------------
    def crop_face(self, frame_bgr):
        img = Image.fromarray(frame_bgr[:, :, ::-1])  # BGR → RGB PIL

        boxes, probs = self.mtcnn.detect(img)
        if boxes is None:
            return None

        # Lấy mặt lớn nhất (box rộng nhất)
        boxes = np.array(boxes)
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        box = boxes[np.argmax(areas)]

        x1, y1, x2, y2 = [int(b) for b in box]
        return img.crop((x1, y1, x2, y2))

    # -------------------------------------------------------------
    # Convert face PIL -> embedding (512 floats)
    # -------------------------------------------------------------
    def embed(self, face_pil):
        if face_pil is None:
            return None

        face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model(face_tensor).cpu().numpy().reshape(-1)

        # Đổi sang float32 (bắt buộc nếu lưu DB & realtime matching)
        emb = emb.astype("float32")

        # L2 normalize 2 lần → embedding ổn định hơn
        emb = emb / (np.linalg.norm(emb) + 1e-10)
        emb = emb / (np.linalg.norm(emb) + 1e-10)

        return emb  # (512,)

    # -------------------------------------------------------------
    def get_embedding(self, img_bgr):
        face = self.crop_face(img_bgr)
        if face is None:
            return None
        return self.embed(face)

    # -------------------------------------------------------------
    def get_embedding_from_pil(self, face_pil):
        return self.embed(face_pil)

    # -------------------------------------------------------------
    # Batch embedding
    # -------------------------------------------------------------
    def batch_embed(self, faces_pil):
        if len(faces_pil) == 0:
            return np.array([])

        batch = torch.stack([self.transform(f) for f in faces_pil]).to(self.device)

        with torch.no_grad():
            emb = self.model(batch).cpu().numpy()

        # Normalize all
        emb = emb.astype("float32")
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10)

        return emb

