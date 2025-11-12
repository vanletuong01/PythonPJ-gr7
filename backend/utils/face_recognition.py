import cv2
import numpy as np
from typing import Optional, Tuple
import pickle

class FaceRecognition:
    """Module nhận diện khuôn mặt đơn giản sử dụng OpenCV và numpy"""
    
    def __init__(self):
        # Sử dụng Haar Cascade để detect face
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Sử dụng LBPH Face Recognizer để tạo embedding đơn giản
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    def detect_face(self, image_path: str) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Phát hiện khuôn mặt trong ảnh
        
        Returns:
            Tuple of (face_image, (x, y, w, h)) hoặc None nếu không tìm thấy
        """
        try:
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                print(f"Không thể đọc ảnh: {image_path}")
                return None
            
            # Convert sang grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                print("Không phát hiện khuôn mặt trong ảnh")
                return None
            
            # Lấy khuôn mặt đầu tiên (lớn nhất)
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            x, y, w, h = faces[0]
            
            # Crop khuôn mặt
            face_image = gray[y:y+h, x:x+w]
            
            # Resize về kích thước chuẩn
            face_image = cv2.resize(face_image, (200, 200))
            
            return face_image, (x, y, w, h)
            
        except Exception as e:
            print(f"Lỗi detect_face: {e}")
            return None
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        Trích xuất embedding từ ảnh khuôn mặt
        Sử dụng histogram của ảnh làm embedding đơn giản
        
        Returns:
            numpy array embedding
        """
        try:
            # Normalize ảnh
            face_image = cv2.equalizeHist(face_image)
            
            # Tạo embedding đơn giản từ histogram
            # Chia ảnh thành grid 8x8 và tính histogram cho mỗi cell
            h, w = face_image.shape
            cell_h, cell_w = h // 8, w // 8
            
            embedding = []
            for i in range(8):
                for j in range(8):
                    cell = face_image[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    hist = cv2.calcHist([cell], [0], None, [16], [0, 256])
                    embedding.extend(hist.flatten())
            
            embedding = np.array(embedding, dtype=np.float32)
            
            # Normalize embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            print(f"Lỗi extract_embedding: {e}")
            return None
    
    def extract_embedding_from_path(self, image_path: str) -> Optional[np.ndarray]:
        """
        Trích xuất embedding từ đường dẫn ảnh
        
        Returns:
            numpy array embedding hoặc None
        """
        result = self.detect_face(image_path)
        if result is None:
            return None
        
        face_image, _ = result
        return self.extract_embedding(face_image)
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        So sánh 2 embeddings
        
        Returns:
            Confidence score (0-1), càng cao càng giống
        """
        try:
            # Tính cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            cosine_sim = dot_product / (norm1 * norm2)
            
            # Convert về range [0, 1]
            confidence = (cosine_sim + 1) / 2
            
            return float(confidence)
            
        except Exception as e:
            print(f"Lỗi compare_embeddings: {e}")
            return 0.0
    
    def find_best_match(self, query_embedding: np.ndarray, 
                       stored_embeddings: list) -> Tuple[Optional[int], float]:
        """
        Tìm embedding khớp nhất từ danh sách
        
        Args:
            query_embedding: Embedding cần tìm
            stored_embeddings: List of (id, embedding) tuples
        
        Returns:
            Tuple of (best_match_id, confidence_score)
        """
        if not stored_embeddings:
            return None, 0.0
        
        best_id = None
        best_confidence = 0.0
        
        for db_id, stored_embedding in stored_embeddings:
            confidence = self.compare_embeddings(query_embedding, stored_embedding)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_id = db_id
        
        return best_id, best_confidence
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Chuyển embedding thành bytes để lưu vào database"""
        return pickle.dumps(embedding)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """Chuyển bytes từ database thành embedding"""
        return pickle.loads(embedding_bytes)
