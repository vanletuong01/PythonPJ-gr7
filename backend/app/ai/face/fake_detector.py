# fake_detector.py
import collections
import numpy as np
import cv2
import torch
from facenet_pytorch import MTCNN
from PIL import Image
import time

class FakeDetector:
    def __init__(self,
                 device=None,
                 anti_spoof_model_path=None,   # optional: path to a PyTorch model that outputs score in [0,1]
                 w_a=0.7, w_b=0.3,
                 window_size=15,
                 smooth_windows=3,
                 threshold_real=0.65):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(keep_all=False, device=self.device)
        self.anti_spoof_model = None
        if anti_spoof_model_path:
            self.load_anti_spoof_model(anti_spoof_model_path)
        self.w_a = w_a
        self.w_b = w_b
        self.W = window_size
        self.smooth_W = smooth_windows
        self.TH = threshold_real
        # Buffers for motion-based features
        self.nose_history = collections.deque(maxlen=self.W)
        self.left_eye_history = collections.deque(maxlen=self.W)
        self.right_eye_history = collections.deque(maxlen=self.W)
        self.frame_scores = collections.deque(maxlen=self.W)
        self.real_conf_history = collections.deque(maxlen=1000)  # long history for smooth check

    def load_anti_spoof_model(self, path):
        # expect a PyTorch model which on forward returns a score or tensor
        model = torch.load(path, map_location=self.device)
        model.eval()
        self.anti_spoof_model = model

    def score_frame_anti_spoof(self, frame, face_box=None):
        """
        If anti_spoof_model present, run model on face crop and return score in [0,1].
        Otherwise fallback heuristic: use Laplacian variance (texture) and color variance. 
        """
        if face_box is not None:
            x1,y1,x2,y2 = face_box
            crop = frame[y1:y2, x1:x2]
        else:
            crop = frame
        if self.anti_spoof_model is not None:
            # convert crop to tensor and forward (user model must match preprocessing)
            img = Image.fromarray(crop[:,:,::-1])
            import torchvision.transforms as transforms
            trans = transforms.Compose([transforms.Resize((128,128)),
                                        transforms.ToTensor(),
                                        transforms.Normalize([0.5]*3,[0.5]*3)])
            x = trans(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out = self.anti_spoof_model(x)
            # assume output is single logit or probability
            if isinstance(out, torch.Tensor):
                score = torch.sigmoid(out).item() if out.numel()==1 else float(out.squeeze().cpu().numpy()[0])
            else:
                score = float(out)
            # clamp
            score = float(np.clip(score, 0.0, 1.0))
            return score
        else:
            # fallback heuristic
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            col_var = np.var(crop.astype(np.float32) / 255.0)
            # normalize heuristics to [0,1] via hand-tuned params
            s_lap = np.tanh(lap_var/100.0)  # more texture => more likely real
            s_col = np.tanh(col_var*5.0)
            score = 0.6*s_lap + 0.4*s_col
            return float(np.clip(score, 0.0, 1.0))

    def update_landmarks(self, landmarks):
        # landmarks can be array shape (5,2) -> left_eye, right_eye, nose, mouth_left, mouth_right
        if landmarks is None:
            # push zeros to maintain window
            self.nose_history.append((0,0))
            self.left_eye_history.append((0,0))
            self.right_eye_history.append((0,0))
            return
        # according to facenet-pytorch ordering: [left_eye, right_eye, nose, mouth_left, mouth_right]
        left, right, nose, ml, mr = landmarks
        self.nose_history.append(tuple(nose))
        self.left_eye_history.append(tuple(left))
        self.right_eye_history.append(tuple(right))

    def score_motion_based(self):
        # compute head movement score and blink-like score
        if len(self.nose_history) < max(3, int(self.W/3)):
            return 0.0
        nose_arr = np.array(self.nose_history, dtype=np.float32)
        left_arr = np.array(self.left_eye_history, dtype=np.float32)
        right_arr = np.array(self.right_eye_history, dtype=np.float32)
        # Head movement: normalized std of nose positions (x,y) relative to frame size approx
        # we normalize by max dimension estimated from history range
        if np.all(nose_arr==0):
            head_movement = 0.0
        else:
            std = np.std(nose_arr, axis=0).mean()
            # normalize (heuristic): assume frame dims ~ 1 after landmark units (they are in pixel coords)
            head_movement = np.tanh(std/10.0)  # bigger -> more movement -> more likely real
        # Blink detection (heuristic): measure vertical displacement between eyes and nose over time
        # compute eye-nose vertical distance changes: quick drops might indicate blink
        eye_mid = (left_arr + right_arr) / 2.0
        d = np.linalg.norm(eye_mid - nose_arr, axis=1)  # vector of distances
        # blink if there is a sudden decrease in eye-nose distance (eyes closed)
        if d.size < 3:
            blink_rate = 0.0
        else:
            diff = -np.diff(d)  # positive if d decreases
            # count significant drops
            drops = (diff > (np.mean(d)*0.07)).sum()
            blink_rate = np.clip(drops / max(1, len(diff)), 0.0, 1.0)
        # Combine head movement and blink heuristics
        score_b = 0.7 * head_movement + 0.3 * blink_rate
        return float(np.clip(score_b, 0.0, 1.0))

    def process_frame(self, frame):
        """
        Main entry: pass BGR frame -> returns dict with:
        {
          "is_real":bool,
          "real_conf":float,
          "score_a":float,
          "score_b":float,
          "face_box": (x1,y1,x2,y2) or None,
          "landmarks": landmarks or None
        }
        """
        img = Image.fromarray(frame[:,:,::-1])
        boxes, probs = self.mtcnn.detect(img, landmarks=True)
        face_box = None
        landmarks = None
        score_a = 0.0
        score_b = 0.0
        if boxes is None or len(boxes)==0:
            # no face detected
            self.update_landmarks(None)
            score_b = self.score_motion_based()
            # anti-spoof unknown -> low
            score_a = 0.0
        else:
            # use first face
            box = boxes[0] if isinstance(boxes, np.ndarray) and boxes.ndim==2 else boxes[0]
            x1,y1,x2,y2 = [int(v) for v in box]
            face_box = (x1,y1,x2,y2)
            # landmarks from detect: shape (5,2)
            # facenet-pytorch returns landmarks array corresponding to boxes; get first
            try:
                landmarks = probs = None
                # get landmarks by calling detect with landmarks=True earlier: facenet sometimes returns tuple
                # Try to get landmarks via mtcnn forward (more robust)
                _, probs_land = self.mtcnn.detect(img, landmarks=True)
                # fallback:
            except Exception:
                pass
            # Instead use mtcnn's forward to get boxes, probs, landmarks:
            try:
                boxes2, probs2, landmarks_arr = self.mtcnn.detect(img, landmarks=True)
                if landmarks_arr is not None and len(landmarks_arr)>0:
                    landmarks = landmarks_arr[0]  # shape (5,2)
            except Exception:
                landmarks = None
            self.update_landmarks(landmarks)
            # score A
            score_a = self.score_frame_anti_spoof(frame, face_box=face_box)
            # score B
            score_b = self.score_motion_based()

        real_conf = self.w_a * score_a + self.w_b * score_b
        self.frame_scores.append(real_conf)
        # smoothing: moving average over last W
        smoothed = np.mean(list(self.frame_scores)) if len(self.frame_scores)>0 else real_conf
        self.real_conf_history.append(smoothed)
        # check acceptance: require smoothed >= TH for at least M consecutive windows
        # We'll return is_real True if last 'smooth_windows' smoothed windows >= TH
        recent = list(self.real_conf_history)[-self.smooth_W:]
        is_real = (len(recent) >= self.smooth_W) and all([r >= self.TH for r in recent])
        return {
            "is_real": bool(is_real),
            "real_conf": float(smoothed),
            "score_a": float(score_a),
            "score_b": float(score_b),
            "face_box": face_box,
            "landmarks": landmarks
        }
