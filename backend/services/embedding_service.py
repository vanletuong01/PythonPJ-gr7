"""
Embedding Service - Centralize tất cả logic liên quan sinh/load/so khớp embeddings
Tái sử dụng DeepFace, MTCNN, xử lý vectors ở một chỗ.
"""
from typing import Optional, Tuple, List
import numpy as np
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import os

from db.repositories.attendent_repo import EmbeddingRepository


class EmbeddingService:
    """Service xử lý logic embedding (sinh, load, so khớp, chuẩn hóa)"""

    EMBEDDING_DIM = 512  # ArcFace embedding = 512 chiều
    THRESHOLD_COSINE = 0.45

    @staticmethod
    def extract_embedding_from_image(image_path: str) -> Optional[np.ndarray]:
        """
        Sinh embedding từ ảnh bằng DeepFace ArcFace.
        Trả về embedding 512 chiều, normalized.
        """
        try:
            result = DeepFace.represent(
                img_path=image_path,
                model_name="ArcFace",
                enforce_detection=False,
                detector_backend="skip"  # Giả sử ảnh đã được cắt
            )

            if result and len(result) > 0 and "embedding" in result[0]:
                emb = np.array(result[0]["embedding"], dtype=np.float32)
                if emb.size == EmbeddingService.EMBEDDING_DIM:
                    emb = emb / (np.linalg.norm(emb) + 1e-9)
                    return emb
                else:
                    print(f"⚠️ Embedding có kích thước khác {EmbeddingService.EMBEDDING_DIM} ({emb.size})")
                    return None
            else:
                print("[⚠️] DeepFace không trả về embedding hợp lệ.")
                return None

        except Exception as e:
            print(f"[❌] Lỗi khi tạo embedding: {e}")
            return None

    @staticmethod
    def extract_embeddings_from_folder(folder_path: str) -> List[np.ndarray]:
        """
        Sinh embeddings từ tất cả ảnh trong thư mục.
        Trả về list embeddings normalized.
        """
        embeddings = []
        if not os.path.exists(folder_path):
            print(f"❌ Thư mục không tồn tại: {folder_path}")
            return embeddings

        for img_name in sorted(os.listdir(folder_path)):
            if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            img_path = os.path.join(folder_path, img_name)
            emb = EmbeddingService.extract_embedding_from_image(img_path)
            if emb is not None:
                embeddings.append(emb)
            else:
                print(f"⚠️ Bỏ qua ảnh: {img_name}")

        return embeddings

    @staticmethod
    def compute_average_embedding(embeddings: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        Tính embedding trung bình từ danh sách embeddings.
        Trả về embedding chuẩn hóa.
        """
        if not embeddings:
            print("❌ Không có embedding nào để tính trung bình.")
            return None

        mean_emb = np.mean(embeddings, axis=0, dtype=np.float32)
        mean_emb = mean_emb / (np.linalg.norm(mean_emb) + 1e-9)
        return mean_emb

    @staticmethod
    def load_all_known_embeddings() -> Tuple[np.ndarray, List[dict]]:
        """
        Load tất cả embeddings từ DB.
        Trả về (embeddings_matrix, metadata_list).
        """
        return EmbeddingRepository.get_all_embeddings()

    @staticmethod
    def find_best_match(
        query_embedding: np.ndarray,
        known_embeddings: np.ndarray,
        metadata: List[dict],
        threshold: float = 0.45
    ) -> Tuple[Optional[dict], float]:
        """
        So khớp query_embedding với tất cả known_embeddings.
        Trả về (best_match_metadata, best_similarity_score).
        """
        if known_embeddings.size == 0:
            print("⚠️ Không có embedding nào trong DB.")
            return None, 0.0

        # Normalize query
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)

        # Tính cosine similarity
        similarities = cosine_similarity([query_embedding], known_embeddings)[0]
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])

        if best_score < threshold:
            print(f"⚠️ Best match score ({best_score:.3f}) < threshold ({threshold})")
            return None, best_score

        best_metadata = metadata[best_idx] if best_idx < len(metadata) else None
        return best_metadata, best_score

    @staticmethod
    def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        """Chuẩn hóa embedding L2."""
        norm = np.linalg.norm(embedding)
        if norm == 0 or np.isnan(norm):
            print("❌ Embedding không hợp lệ (norm=0 hoặc NaN).")
            return embedding
        return embedding / norm
