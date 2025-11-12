from fastapi import APIRouter, UploadFile, Form, Query
from fastapi.responses import JSONResponse
import os, traceback, numpy as np
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
from db.repositories.embeddings_repo import insert_embedding
from core.face_app.load_embeddings import load_embeddings_from_mysql
from db.database import get_connection

router = APIRouter(prefix="/api/face", tags=["Face Recognition"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data/face")
os.makedirs(DATA_DIR, exist_ok=True)

# =========================================================
# 1️⃣ API: Lưu frame khi đăng ký
# =========================================================
@router.post("/register")
async def register_frame(
    student_code: str = Form(...),
    full_name: str = Form(""),
    index: int = Form(0),
    photo: UploadFile = None
):
    try:
        if not student_code:
            return JSONResponse({"status": "error", "message": "Thiếu mã sinh viên"})

        student_folder = os.path.join(DATA_DIR, student_code)
        os.makedirs(student_folder, exist_ok=True)

        if photo is None:
            return JSONResponse({"status": "error", "message": "Không có file ảnh gửi lên"})

        save_path = os.path.join(student_folder, f"frame_{index}.jpg")
        with open(save_path, "wb") as f:
            f.write(await photo.read())

        print(f"📸 Ảnh {index} đã lưu: {save_path}")
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print("❌ Lỗi register_frame:\n", traceback.format_exc())
        return JSONResponse({"status": "error", "message": str(e)})


# =========================================================
# 2️⃣ API: Hoàn tất đăng ký
# =========================================================
@router.get("/finalize")
async def finalize_register(student_code: str = Query(...), full_name: str = Query("")):
    try:
        student_folder = os.path.join(DATA_DIR, student_code)
        if not os.path.exists(student_folder):
            return JSONResponse({"status": "error", "message": "Không tìm thấy thư mục ảnh."})

        image_files = [
            os.path.join(student_folder, f)
            for f in os.listdir(student_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not image_files:
            return JSONResponse({"status": "error", "message": "Không có ảnh hợp lệ trong thư mục."})

        embeddings = []
        print(f"⚙️ Tính embedding cho {len(image_files)} ảnh...")

        for i, img_path in enumerate(image_files, start=1):
            try:
                result = DeepFace.represent(
                    img_path=img_path,
                    model_name="ArcFace",
                    detector_backend="mtcnn",
                    enforce_detection=False
                )
                if result:
                    embeddings.append(result[0]["embedding"])
                    print(f"✅ Ảnh {i}/{len(image_files)} xử lý xong")
            except Exception as e:
                print(f"⚠️ Bỏ qua ảnh lỗi {img_path}: {e}")

        if not embeddings:
            return JSONResponse({"status": "error", "message": "Không có ảnh nào được xử lý thành công."})

        avg_embedding = np.mean(embeddings, axis=0, dtype=np.float32)
        insert_embedding(student_code, avg_embedding, photo_path=student_folder, full_name=full_name)

        print(f"🎉 Đăng ký thành công cho {student_code} - {full_name}")
        return JSONResponse({"status": "success", "message": f"✅ Đăng ký thành công {full_name} ({len(embeddings)} ảnh)!"})
    except Exception as e:
        print("❌ Lỗi finalize_register:\n", traceback.format_exc())
        return JSONResponse({"status": "error", "message": str(e)})


# =========================================================
# 3️⃣ API: Điểm danh
# =========================================================
@router.post("/check")
async def check_face(photo: UploadFile):
    try:
        temp_path = os.path.join(BASE_DIR, "../../temp.jpg")
        with open(temp_path, "wb") as f:
            f.write(await photo.read())

        result = DeepFace.represent(
            img_path=temp_path,
            model_name="ArcFace",
            detector_backend="mtcnn",
            enforce_detection=False
        )
        if not result:
            return JSONResponse({"status": "error", "message": "Không phát hiện được khuôn mặt."})

        input_embedding = np.array(result[0]["embedding"], dtype=np.float32).reshape(1, -1)
        input_embedding /= np.linalg.norm(input_embedding) + 1e-9

        known_faces, known_ids = load_embeddings_from_mysql()
        if known_faces.size == 0:
            return JSONResponse({"status": "error", "message": "Chưa có sinh viên nào trong DB."})

        sims = cosine_similarity(input_embedding, known_faces)[0]
        best_idx = np.argmax(sims)
        best_score = sims[best_idx]
        best_id = known_ids[best_idx]
        print(f"🔍 Tương đồng cao nhất: {best_score:.3f} (StudentID={best_id})")

        if best_score < 0.5:
            return JSONResponse({"status": "not_found", "message": "Không khớp với sinh viên nào."})

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT FullName, StudentCode FROM student WHERE StudentID = %s", (best_id,))
        student = cursor.fetchone()
        cursor.execute("SELECT StudyID FROM study WHERE StudentID = %s LIMIT 1", (best_id,))
        study = cursor.fetchone()

        if not study or not study.get("StudyID"):
            cursor.close()
            conn.close()
            return JSONResponse({"status": "error", "message": "Không tìm thấy buổi học (StudyID)"})

        study_id = study["StudyID"]
        cursor.execute("""
            INSERT INTO attendance (StudyID, Date, Time, PhotoPath)
            VALUES (%s, CURDATE(), CURTIME(), %s)
        """, (study_id, temp_path))
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ Điểm danh thành công: {student['StudentCode']} - {student['FullName']} ({best_score:.3f})")
        return JSONResponse({
            "status": "success",
            "student": {
                "student_code": student["StudentCode"],
                "full_name": student["FullName"]
            },
            "similarity": round(float(best_score), 3)
        })
    except Exception as e:
        print("❌ Lỗi check_face:\n", traceback.format_exc())
        return JSONResponse({"status": "error", "message": str(e)})
