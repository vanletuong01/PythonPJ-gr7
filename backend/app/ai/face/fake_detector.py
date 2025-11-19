import numpy as np
import cv2
import torch
from PIL import Image
from facenet_pytorch import MTCNN
import collections
import torchvision.transforms as transforms


class FakeDetector:
    def __init__(self,
                 device=None,
                 anti_spoof_model_path=None,
                 w_a=0.65,
                 w_b=0.35,
                 window_size=12,
                 smooth_windows=4,
                 threshold_real=0.63):

        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        self.mtcnn = MTCNN(keep_all=False, device=self.device, post_process=False)

        self.anti_spoof_model = None
        if anti_spoof_model_path:
            model = torch.load(anti_spoof_model_path, map_location=self.device)
            model.eval()
            self.anti_spoof_model = model

        self.w_a = w_a
        self.w_b = w_b
        self.W = window_size
        self.smooth_W = smooth_windows
        self.TH = threshold_real

        self.nose_hist = collections.deque(maxlen=self.W)
        self.eye_hist = collections.deque(maxlen=self.W)
        self.conf_hist = collections.deque(maxlen=150)

    # -----------------------
    # Anti-spoof score
    # -----------------------
    def score_frame_anti_spoof(self, frame, box):
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]

        # nếu có model anti-spoof
        if self.anti_spoof_model:
            img = Image.fromarray(crop[:, :, ::-1])
            trans = transforms.Compose([
                transforms.Resize((128,128)),
                transforms.ToTensor(),
                transforms.Normalize([0.5]*3, [0.5]*3)
            ])
            x = trans(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out = self.anti_spoof_model(x)

            score = torch.sigmoid(out).item()
            return float(np.clip(score, 0, 1))

        # fallback texture
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F).var()
        col = np.var(crop.astype(np.float32) / 255.0)

        s1 = np.tanh(lap / 80)
        s2 = np.tanh(col * 4)
        return float(np.clip(0.6 * s1 + 0.4 * s2, 0, 1))

    # -----------------------
    def update_landmarks(self, lm):
        if lm is None:
            self.nose_hist.append((0, 0))
            self.eye_hist.append((0, 0))
            return

        left, right, nose, *_ = lm
        mid = (left + right) / 2.0

        self.nose_hist.append(tuple(nose))
        self.eye_hist.append(tuple(mid))

    # -----------------------
    def score_motion(self):
        if len(self.nose_hist) < 4:
            return 0.0

        nose = np.array(self.nose_hist)
        eye = np.array(self.eye_hist)

        head_std = np.std(nose, axis=0).mean()
        head_score = np.tanh(head_std / 8.0)

        d = np.linalg.norm(nose - eye, axis=1)
        diff = -np.diff(d)
        blink = (diff > np.mean(d) * 0.06).sum()
        blink_score = np.clip(blink / max(1, len(diff)), 0, 1)

        return float(0.7 * head_score + 0.3 * blink_score)

    # -----------------------
    def process_frame(self, frame):
        img = Image.fromarray(frame[:, :, ::-1])

        boxes, probs, landmarks = self.mtcnn.detect(img, landmarks=True)

        if boxes is None:
            self.update_landmarks(None)
            anti = 0.0
            motion = self.score_motion()
        else:
            box = [int(x) for x in boxes[0]]
            lm = landmarks[0] if landmarks is not None else None

            self.update_landmarks(lm)

            anti = self.score_frame_anti_spoof(frame, box)
            motion = self.score_motion()

        conf = self.w_a * anti + self.w_b * motion
        self.conf_hist.append(conf)

        smooth = np.mean(list(self.conf_hist)[-self.smooth_W:])
        is_real = smooth >= self.TH

        return {
            "is_real": bool(is_real),
            "real_conf": float(smooth),
            "score_a": float(anti),
            "score_b": float(motion)
        }
