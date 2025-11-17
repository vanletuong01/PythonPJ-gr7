# capture_faces.py
import cv2
import time
import numpy as np
from arcface_embedder import ArcfaceEmbedder
from face_db import FaceDB
from facenet_pytorch import MTCNN
from PIL import Image

def capture_and_register(student_id, name, db_config=None, num_photos=25, cam_index=0):
    db = FaceDB(**(db_config or {}))
    embedder = ArcfaceEmbedder()
    mtcnn = MTCNN(keep_all=False, device=embedder.device)
    cap = cv2.VideoCapture(cam_index)
    captured = 0
    embeddings = []
    print("Bắt đầu chụp ảnh. Nhìn thẳng vào camera ...")
    while captured < num_photos:
        ret, frame = cap.read()
        if not ret:
            print("Không đọc được camera")
            break
        # Show guide
        cv2.putText(frame, f"Capturing {captured}/{num_photos}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Capture", frame)
        key = cv2.waitKey(1)
        # Detect face via MTCNN fast detection (use facenet-pytorch detect)
        img = Image.fromarray(frame[:,:,::-1])
        boxes, probs = mtcnn.detect(img)
        if boxes is not None and len(boxes)>0:
            # Crop first box
            x1, y1, x2, y2 = [int(b) for b in boxes[0]]
            crop = img.crop((x1,y1,x2,y2))
            emb = embedder.embed(crop)
            embeddings.append(emb)
            captured += 1
            time.sleep(0.2)  # small delay to get slightly different poses
        # allow user to quit
        if key == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    if len(embeddings) == 0:
        print("Không có embedding nào được tạo")
        return False
    # average embeddings
    mean_emb = np.mean(np.stack(embeddings, axis=0), axis=0)
    mean_emb = mean_emb / np.linalg.norm(mean_emb)
    db.insert_embedding(student_id, name, mean_emb)
    db.close()
    print(f"Đã lưu embedding cho {student_id} - {name}")
    return True

if __name__ == "__main__":
    # Example usage
    capture_and_register("SV001", "Nguyen Van A", db_config={"host":"localhost","user":"root","password":"","database":"face_db"})
