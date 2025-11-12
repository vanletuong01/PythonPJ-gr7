# Hệ thống Điểm danh Sinh viên bằng Nhận diện Khuôn mặt

## Mô tả dự án

Hệ thống điểm danh sinh viên tự động sử dụng công nghệ nhận diện khuôn mặt, được xây dựng bằng Python.

### Kiến trúc hệ thống

- **Backend**: FastAPI - xử lý API, lưu trữ ảnh và embedding
- **Database**: MySQL (XAMPP) - lưu metadata và face embeddings  
- **Frontend**: Streamlit - giao diện người dùng
- **Face Recognition**:  - nhận diện khuôn mặt đơn giản
- **Storage**: Server filesystem cho ảnh

### Đặc điểm chính

Server-side inference - mọi xử lý đều ở server  
Client chỉ upload ảnh qua API, không truy cập trực tiếp DB/filesystem   
Lưu embeddings trong MySQL (dạng BLOB)  

### Cài đặt dependencies
```bash
pip install -r requirements.txt
```

## 🎯 Chạy ứng dụng

### Bước 1: Khởi động Backend (FastAPI)

Mở terminal/cmd thứ nhất:

```bash
# Kích hoạt virtualenv nếu chưa
& D:/PythonPJ/.venv/Scripts/Activate.ps1

# Vào thư mục project nếu cần
cd D:\PythonPJ\PythonPJ

# Chạy backend (sửa lại đường dẫn nếu cần)
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

Kiểm tra API: http://localhost:8000/docs (Swagger UI)

### Bước 2: Khởi động Frontend (Streamlit)

Mở terminal/cmd thứ hai:

```bash
# Kích hoạt virtualenv nếu chưa
& D:/PythonPJ/.venv/Scripts/Activate.ps1

# Vào thư mục frontend
cd D:\PythonPJ\PythonPJ

# Chạy Streamlit app
python -m streamlit run frontend/app.py
```
Frontend sẽ mở tự động tại: http://localhost:8501

## Hướng dẫn sử dụng

### 1. Đăng ký sinh viên
- Vào menu "Đăng ký sinh viên"
- Điền thông tin: Mã SV, Họ tên, Lớp, Email, SĐT
- Upload ảnh khuôn mặt (chân dung, rõ nét, 1 người)
- Click "Đăng ký"

### 2. Điểm danh
- Vào menu "Điểm danh"
- Chọn "Chụp ảnh" hoặc "Upload ảnh"
- Hệ thống tự động nhận diện và điểm danh

### 3. Xem danh sách sinh viên
- Vào menu "Danh sách sinh viên"
- Tìm kiếm theo mã sinh viên
- Xem lịch sử điểm danh

### 4. Báo cáo điểm danh
- Vào menu "Báo cáo điểm danh"
- Xem điểm danh hôm nay
- Tải xuống file CSV

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

## Lưu ý

- Đảm bảo XAMPP MySQL đang chạy trước khi start backend
- Ảnh khuôn mặt nên rõ nét, đủ sáng
- Không nên có nhiều người cùng mã sinh viên
- Backend phải chạy trước khi mở Frontend

## Xử lý lỗi thường gặp

### "Không phát hiện khuôn mặt"
- Ảnh quá tối/mờ
- Khuôn mặt quá nhỏ trong ảnh

### "Không kết nối được database"
- Kiểm tra XAMPP MySQL đã chạy chưa
- Kiểm tra cấu hình trong `config.py`

### "Module not found"
- Chạy lại: `pip install -r requirements.txt`

## 📝 Phát triển thêm

Có thể mở rộng:
- Thêm xác thực người dùng
- Export báo cáo Excel
- Gửi email/thông báo tự động
- Tích hợp camera IP
- Dashboard analytics nâng cao