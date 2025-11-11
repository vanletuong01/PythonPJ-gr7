# Hệ thống Điểm danh Sinh viên bằng Nhận diện Khuôn mặt

## 📋 Mô tả dự án

Hệ thống điểm danh sinh viên tự động sử dụng công nghệ nhận diện khuôn mặt, được xây dựng hoàn toàn bằng Python.

### 🏗️ Kiến trúc hệ thống

- **Backend**: FastAPI - xử lý API, lưu trữ ảnh và embedding
- **Database**: MySQL (XAMPP) - lưu metadata và face embeddings  
- **Frontend**: Streamlit - giao diện người dùng
- **Face Recognition**: OpenCV + NumPy - nhận diện khuôn mặt đơn giản
- **Storage**: Server filesystem cho ảnh

### 🔑 Đặc điểm chính

✅ Server-side inference - mọi xử lý đều ở server  
✅ Client chỉ upload ảnh qua API, không truy cập trực tiếp DB/filesystem  
✅ Lưu embeddings trong MySQL (dạng BLOB)  
✅ Matching đơn giản bằng NumPy (cosine similarity)  
✅ Thuần Python - phù hợp cho môn học lập trình Python  

## 📁 Cấu trúc thư mục

```
PythonPJ/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── database.py                  # Database connection & init
│   ├── config.py                    # Cấu hình hệ thống
│   └── face_recognition_module.py   # Module nhận diện khuôn mặt
├── frontend/
│   └── app.py                       # Streamlit application
├── uploads/
│   ├── student_images/              # Ảnh đăng ký sinh viên
│   └── attendance_images/           # Ảnh điểm danh
├── requirements.txt                 # Python dependencies
└── README.md
```

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt Python
- Yêu cầu: Python 3.8 trở lên
- Download tại: https://www.python.org/downloads/

### 2. Cài đặt XAMPP
- Download XAMPP: https://www.apachefriends.org/
- Khởi động Apache và MySQL trong XAMPP Control Panel

### 3. Clone/Download dự án
```bash
cd d:\PythonPJ
```

### 4. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 5. Khởi tạo database
```bash
python backend/database.py
```

Lệnh này sẽ tạo:
- Database: `attendance_system`
- Bảng: `students`, `face_embeddings`, `attendance`

## 🎯 Chạy ứng dụng

### Bước 1: Khởi động Backend (FastAPI)

Mở terminal/cmd thứ nhất:

```bash
cd d:\PythonPJ\backend
python main.py
```

Backend sẽ chạy tại: http://localhost:8000

Kiểm tra API: http://localhost:8000/docs (Swagger UI)

### Bước 2: Khởi động Frontend (Streamlit)

Mở terminal/cmd thứ hai:

```bash
cd d:\PythonPJ\frontend
streamlit run app.py
```

Frontend sẽ mở tự động tại: http://localhost:8501

## 📖 Hướng dẫn sử dụng

### 1. Đăng ký sinh viên
- Vào menu "➕ Đăng ký sinh viên"
- Điền thông tin: Mã SV, Họ tên, Lớp, Email, SĐT
- Upload ảnh khuôn mặt (chân dung, rõ nét, 1 người)
- Click "Đăng ký"

### 2. Điểm danh
- Vào menu "✅ Điểm danh"
- Chọn "Chụp ảnh" hoặc "Upload ảnh"
- Hệ thống tự động nhận diện và điểm danh

### 3. Xem danh sách sinh viên
- Vào menu "👥 Danh sách sinh viên"
- Tìm kiếm theo mã sinh viên
- Xem lịch sử điểm danh

### 4. Báo cáo điểm danh
- Vào menu "📊 Báo cáo điểm danh"
- Xem điểm danh hôm nay
- Tải xuống file CSV

## 🔧 Cấu hình

### Database (backend/config.py)
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # XAMPP mặc định không có password
    "database": "attendance_system"
}
```

### Face Recognition
```python
CONFIDENCE_THRESHOLD = 0.6  # Ngưỡng nhận diện (0-1)
MAX_FACE_DISTANCE = 0.6     # Khoảng cách tối đa
```

## 🗄️ Database Schema

### Bảng `students`
- `id`: INT (Primary Key)
- `student_id`: VARCHAR(20) (Unique)
- `full_name`: VARCHAR(100)
- `class_name`: VARCHAR(50)
- `email`: VARCHAR(100)
- `phone`: VARCHAR(20)
- `image_path`: VARCHAR(255)
- `created_at`, `updated_at`: TIMESTAMP

### Bảng `face_embeddings`
- `id`: INT (Primary Key)
- `student_id`: VARCHAR(20) (Foreign Key)
- `embedding`: BLOB (Face embedding vector)
- `image_path`: VARCHAR(255)
- `created_at`: TIMESTAMP

### Bảng `attendance`
- `id`: INT (Primary Key)
- `student_id`: VARCHAR(20) (Foreign Key)
- `attendance_date`: DATE
- `attendance_time`: TIME
- `status`: VARCHAR(20)
- `confidence_score`: FLOAT
- `image_path`: VARCHAR(255)
- `created_at`: TIMESTAMP

## 🔌 API Endpoints

### Students
- `POST /api/students/register` - Đăng ký sinh viên
- `GET /api/students` - Lấy danh sách sinh viên
- `GET /api/students/{student_id}` - Lấy thông tin sinh viên
- `DELETE /api/students/{student_id}` - Xóa sinh viên

### Attendance
- `POST /api/attendance/checkin` - Điểm danh
- `GET /api/attendance/today` - Điểm danh hôm nay
- `GET /api/attendance/student/{student_id}` - Lịch sử điểm danh

### Statistics
- `GET /api/stats` - Thống kê tổng quan

## 🛠️ Công nghệ sử dụng

- **FastAPI**: Web framework cho Python
- **Streamlit**: Framework tạo web app nhanh
- **MySQL**: Cơ sở dữ liệu quan hệ
- **OpenCV**: Thư viện computer vision
- **NumPy**: Tính toán số học, xử lý array
- **Pillow**: Xử lý ảnh

## 🎓 Nguyên lý hoạt động

### 1. Đăng ký sinh viên
1. Client upload ảnh qua API
2. Server lưu ảnh vào filesystem
3. Detect khuôn mặt bằng Haar Cascade
4. Trích xuất embedding (histogram-based)
5. Lưu embedding vào MySQL (BLOB)

### 2. Điểm danh
1. Client upload ảnh qua API
2. Server detect face và trích xuất embedding
3. So sánh với tất cả embeddings trong DB
4. Tính cosine similarity (NumPy)
5. Tìm match tốt nhất (confidence > threshold)
6. Lưu kết quả điểm danh

## ⚠️ Lưu ý

- Đảm bảo XAMPP MySQL đang chạy trước khi start backend
- Ảnh khuôn mặt nên rõ nét, đủ sáng, chỉ có 1 người
- Không nên có nhiều người cùng mã sinh viên
- Backend phải chạy trước khi mở Frontend

## 🐛 Xử lý lỗi thường gặp

### "Không phát hiện khuôn mặt"
- Ảnh quá tối/mờ
- Khuôn mặt quá nhỏ trong ảnh
- Có nhiều khuôn mặt trong ảnh

### "Không kết nối được database"
- Kiểm tra XAMPP MySQL đã chạy chưa
- Kiểm tra cấu hình trong `config.py`

### "Module not found"
- Chạy lại: `pip install -r requirements.txt`

## 📝 Phát triển thêm

Có thể mở rộng:
- Sử dụng model deep learning (FaceNet, ArcFace) thay vì histogram
- Thêm xác thực người dùng
- Export báo cáo Excel
- Gửi email/thông báo tự động
- Tích hợp camera IP
- Dashboard analytics nâng cao

## 👨‍💻 Tác giả

Dự án môn học Lập trình Python

---

**Chúc bạn thành công! 🎉**
