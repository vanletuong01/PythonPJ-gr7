from facenet_pytorch import MTCNN
import torch
import numpy as np

_device = 'cuda' if torch.cuda.is_available() else 'cpu'

_mtcnn = MTCNN(
    image_size=160,
    margin=10,
    keep_all=True,
    device=_device
)

def detect_faces_rgb(pil_or_np_rgb):
    """
    Return boxes (N,4), probs
    Accept PIL hoặc numpy RGB.
    """
    boxes, probs = _mtcnn.detect(pil_or_np_rgb)
    return boxes, probs

def extract_face_region_rgb(rgb_frame, box):
    """
    box: [x1,y1,x2,y2]
    return crop RGB
    """
    x1, y1, x2, y2 = [int(v) for v in box]
    h, w = rgb_frame.shape[:2]

    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return None

    return rgb_frame[y1:y2, x1:x2]
