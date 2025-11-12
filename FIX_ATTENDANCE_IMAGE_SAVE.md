# ✅ Sửa Lỗi: Không Lưu Ảnh Điểm Danh

## 🐛 Vấn Đề Ban Đầu

```
❌ Lỗi: Error opening 'uploads/attendance_images/attendance_*.jpg'
```

**Nguyên nhân:**
1. Ảnh không được lưu vào disk (chỉ lưu đường dẫn string vào DB)
2. Đường dẫn sai (`photos/` thay vì `uploads/attendance_images/`)
3. Không có ảnh thực tế để hiển thị

---

## ✅ Sửa Đã Làm

### 1️⃣ **smart_face_attendance.py** - Sửa hàm lưu ảnh

**Trước:**
```python
def save_attendance_to_db(self, study_id):
    photo_path = f"photos/{study_id}.jpg"  # ❌ Chỉ lưu string, không lưu file
    self.attendance_repo.insert_attendance(study_id=study_id, photo_path=photo_path)
```

**Sau:**
```python
def save_attendance_to_db(self, study_id, face_image=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_studyid_{study_id}_{timestamp}.jpg"
    
    # Lưu ảnh thực tế vào disk
    if face_image is not None:
        photo_path = os.path.join(ATTENDANCE_IMAGES_DIR, filename)
        cv2.imwrite(photo_path, face_image)  # ✅ Lưu file thực tế!
        logger.info(f"✅ Lưu ảnh: {photo_path}")
    
    self.attendance_repo.insert_attendance(study_id=study_id, photo_path=photo_path)
```

**Thay đổi:**
- ✅ Thêm parameter `face_image` để nhận ảnh
- ✅ Tạo tên file với timestamp (unique)
- ✅ Lưu ảnh thực tế bằng `cv2.imwrite()`
- ✅ Dùng `ATTENDANCE_IMAGES_DIR` từ config
- ✅ Tự tạo thư mục nếu chưa có

---

### 2️⃣ **attendance_service.py** - Truyền ảnh

**Trước:**
```python
meta, score, face_crop = self.face_att.recognize_face(frame)
ok = self.face_att.save_attendance_to_db(study_id=study_id)  # ❌ Không truyền ảnh
```

**Sau:**
```python
meta, score, face_crop = self.face_att.recognize_face(frame)
# Chuyển RGB → BGR để lưu bằng cv2
face_crop_bgr = cv2.cvtColor(face_crop, cv2.COLOR_RGB2BGR) if face_crop is not None else None
ok = self.face_att.save_attendance_to_db(study_id=study_id, face_image=face_crop_bgr)  # ✅ Truyền ảnh!
```

---

## 🎯 Dòng Chảy Hoàn Chỉnh

```
Upload ảnh
  ↓
Nhận diện khuôn mặt → face_crop (RGB)
  ↓
Chuyển RGB → BGR ✅
  ↓
save_attendance_to_db(study_id, face_image)
  ↓
Lưu file: uploads/attendance_images/attendance_studyid_123_20251112_090002.jpg ✅
  ↓
Lưu đường dẫn vào DB (PhotoPath column) ✅
  ↓
✅ Có thể hiển thị ảnh từ đường dẫn này!
```

---

## 📁 Cấu Trúc Thư Mục

```
D:\PythonPJ\
├── backend/
│   ├── uploads/
│   │   ├── attendance_images/        ✅ Thư mục lưu ảnh
│   │   │   ├── attendance_studyid_1_20251112_090002.jpg
│   │   │   ├── attendance_studyid_2_20251112_090015.jpg
│   │   │   └── ...
│   │   └── student_images/
│   └── ...
└── ...
```

---

## 🔍 Database Schema

```sql
CREATE TABLE `attendance` (
  `AttendanceID` int(11) NOT NULL,
  `StudyID` int(11) NOT NULL,
  `Date` date NOT NULL,
  `Time` time NOT NULL,
  `PhotoPath` varchar(255) DEFAULT NULL  ← Lưu đường dẫn ảnh
);
```

**Ví dụ:**
```
AttendanceID | StudyID | Date       | Time     | PhotoPath
1            | 5       | 2025-11-12 | 09:00:02 | uploads/attendance_images/attendance_studyid_5_20251112_090002.jpg
```

---

## ✅ Kiểm Tra

### Sau khi upload ảnh:

**1. Kiểm tra thư mục:**
```powershell
dir backend/uploads/attendance_images/
```

**Kỳ vọng:**
```
attendance_studyid_123_20251112_090002.jpg  ✅ (file thực tế tồn tại)
attendance_studyid_124_20251112_090015.jpg  ✅
```

**2. Kiểm tra database:**
```sql
SELECT * FROM attendance WHERE DATE(Date) = CURDATE();
```

**Kỳ vọng:**
```
AttendanceID | StudyID | Date       | Time     | PhotoPath
1            | 5       | 2025-11-12 | 09:00:02 | uploads/attendance_images/attendance_studyid_5_20251112_090002.jpg
```

**3. Mở ảnh:**
```python
import cv2
img = cv2.imread("uploads/attendance_images/attendance_studyid_5_20251112_090002.jpg")
# ✅ Ảnh được load thành công!
```

---

## 🎉 Tóm Lại

| Trước | Sau |
|------|-----|
| ❌ Không lưu ảnh | ✅ Lưu ảnh thực tế |
| ❌ Đường dẫn sai | ✅ Đường dẫn đúng |
| ❌ Không thể hiển thị | ✅ Có thể hiển thị ảnh |
| ❌ PhotoPath = NULL | ✅ PhotoPath = đúng đường dẫn |

**Giờ upload ảnh xem, ảnh sẽ được lưu vào `uploads/attendance_images/` và có thể hiển thị được! 🎯**
