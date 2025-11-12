"""
Script khởi tạo database cho hệ thống điểm danh
Chạy file này để tạo database và các bảng cần thiết
"""

if __name__ == "__main__":
    print("=" * 60)
    print("KHỞI TẠO DATABASE HỆ THỐNG ĐIỂM DANH SINH VIÊN")
    print("=" * 60)
    print()
    print("📋 Đang tạo database và các bảng...")
    print()
    
    from .database import init_database
    init_database()
    
    print()
    print("=" * 60)
    print("✅ HOÀN TẤT!")
    print("=" * 60)
    print()
    print("Bước tiếp theo:")
    print("1. Khởi động backend: cd backend && python main.py")
    print("2. Khởi động frontend: cd frontend && streamlit run app.py")
    print()
