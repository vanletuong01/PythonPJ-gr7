# arcface_embedder.py
from facenet_pytorch import InceptionResnetV1, MTCNN
import torch
import numpy as np
from PIL import Image
import cv2

class ArcfaceEmbedder:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        # Load pretrained InceptionResnetV1 trained on VGGFace2 (embedding 512)
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        # For detection/face crop we can use MTCNN; but caller may already crop
        self.mtcnn = MTCNN(keep_all=False, device=self.device)

    def crop_face(self, frame):
        """
        frame: numpy BGR (opencv). Return PIL cropped face or None
        """
        img = Image.fromarray(frame[:, :, ::-1])  # BGR->RGB
        boxes, probs = self.mtcnn.detect(img)
        
        if boxes is None or len(boxes) == 0:
            return None
        
        # Lấy face đầu tiên (hoặc lớn nhất)
        box = boxes[0]
        x1, y1, x2, y2 = [int(b) for b in box]
        return img.crop((x1, y1, x2, y2))

    def embed(self, face_pil: Image.Image):
        """
        face_pil: cropped face PIL, convert to tensor as facenet expects
        Returns: 512D normalized embedding
        """
        # Use model's forward after preprocessing: resnet expects 160x160
        face = face_pil.resize((160, 160))
        
        # Convert to torch tensor with same preprocessing as facenet-pytorch expects
        import torchvision.transforms as transforms
        trans = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5]*3, [0.5]*3)
        ])
        x = trans(face).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            emb = self.model(x).cpu().numpy().reshape(-1)
        
        # L2 normalize
        emb = emb / (np.linalg.norm(emb) + 1e-9)
        return emb

    # ===============================
    # PHƯƠNG THỨC MỚI (cho capture service)
    # ===============================
    def get_embedding(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Nhận ảnh BGR (OpenCV), tự động crop face và embed.
        
        Args:
            img_bgr: numpy array BGR (H, W, 3)
        
        Returns:
            512D embedding (normalized) hoặc None nếu không detect được face
        """
        try:
            # Crop face từ ảnh BGR
            face_pil = self.crop_face(img_bgr)
            
            if face_pil is None:
                return None
            
            # Generate embedding
            embedding = self.embed(face_pil)
            
            return embedding
            
        except Exception as e:
            print(f"❌ Error in get_embedding: {e}")
            return None
    
    def get_embedding_from_pil(self, face_pil: Image.Image) -> np.ndarray:
        """
        Nhận face đã crop (PIL), chỉ embed (không detect).
        Dùng khi caller đã tự crop face sẵn.
        
        Args:
            face_pil: PIL Image (face đã crop)
        
        Returns:
            512D embedding (normalized)
        """
        return self.embed(face_pil)
    
    def detect_and_crop_all_faces(self, img_bgr: np.ndarray) -> list:
        """
        Detect tất cả faces trong ảnh (nếu có nhiều người).
        
        Args:
            img_bgr: numpy BGR
        
        Returns:
            List of PIL cropped faces
        """
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        boxes, probs = self.mtcnn.detect(img_pil)
        
        if boxes is None:
            return []
        
        faces = []
        for box in boxes:
            x1, y1, x2, y2 = [int(b) for b in box]
            face = img_pil.crop((x1, y1, x2, y2))
            faces.append(face)
        
        return faces
    
    def batch_embed(self, faces_pil: list) -> np.ndarray:
        """
        Embed nhiều faces cùng lúc (batch processing).
        
        Args:
            faces_pil: List of PIL Images (faces đã crop)
        
        Returns:
            numpy array (N, 512) embeddings
        """
        if len(faces_pil) == 0:
            return np.array([])
        
        import torchvision.transforms as transforms
        trans = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize([0.5]*3, [0.5]*3)
        ])
        
        # Stack thành batch
        batch = torch.stack([trans(f) for f in faces_pil]).to(self.device)
        
        with torch.no_grad():
            embeddings = self.model(batch).cpu().numpy()
        
        # L2 normalize từng embedding
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-9)
        
        return embeddings
