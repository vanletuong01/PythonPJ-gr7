# backend/app/ai/train_faces.py

import os
import cv2
import pickle
import numpy as np
from tqdm import tqdm
from .arcface_model import embed_face

DATA_DIR = "backend/app/data/face"
OUT_FILE = "backend/app/models/face_encodings.pkl"


def train_embeddings():
    names = []
    encs = []
    meta = []

    for folder in sorted(os.listdir(DATA_DIR)):
        path = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(path):
            continue

        person_embs = []

        for f in sorted(os.listdir(path)):
            if not f.lower().endswith((".jpg", ".png", ".jpeg")):
                continue

            img = cv2.imread(os.path.join(path, f))
            if img is None:
                continue

            emb = embed_face(img)
            person_embs.append(emb)

        if len(person_embs) == 0:
            print(f"[SKIP] {folder}: không có ảnh hợp lệ")
            continue

        mean_emb = np.mean(person_embs, axis=0)
        mean_emb /= np.linalg.norm(mean_emb) + 1e-9

        encs.append(mean_emb.astype(np.float32))
        names.append(folder)
        meta.append({"num_images": len(person_embs)})

        print(f"[OK] {folder}: {len(person_embs)} ảnh")

    db = {
        "encodings": np.vstack(encs).astype(np.float32),
        "names": names,
        "meta": meta
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "wb") as f:
        pickle.dump(db, f)

    print("Saved:", OUT_FILE)
