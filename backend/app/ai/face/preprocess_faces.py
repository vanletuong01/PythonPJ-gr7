# preprocess_faces.py
# Các hàm tiền xử lý ảnh (điều chỉnh sáng, làm nét, crop, resize)

import cv2
import numpy as np

def adjust_lighting_brightness(img_bgr):
    """Equalize và gamma random để tăng robustness"""
    img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    balanced = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    # gamma nhẹ
    gamma = 1.0
    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(balanced, table)

def denoise_and_sharpen(img_bgr):
    denoised = cv2.fastNlMeansDenoisingColored(img_bgr, None, 10, 10, 7, 21)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(denoised, -1, kernel)

def resize_face(face_bgr, size=(224,224)):
    """ArcFace (DeepFace) thường chấp nhận nhiều kích thước, 224 ok"""
    return cv2.resize(face_bgr, size)

def preprocess_for_deepface(face_bgr):
    """
    Trả về BGR image đã chuẩn (uint8) phù hợp để truyền cho DeepFace.represent (nếu truyền np array RGB).
    DeepFace.represent chấp nhận numpy RGB array trực tiếp.
    """
    img = adjust_lighting_brightness(face_bgr)
    img = denoise_and_sharpen(img)
    img = resize_face(img, (224,224))
    # DeepFace expects RGB, we'll convert at call site if needed
    return img
