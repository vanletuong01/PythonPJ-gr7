import mysql.connector
from mysql.connector import Error
from backend.db.config import DB_CONFIG


class Database:
    def __init__(self):
        self.host = DB_CONFIG["host"]
        self.user = DB_CONFIG["user"]
        self.password = DB_CONFIG["password"]
        self.database = DB_CONFIG["database"]
        self.port = DB_CONFIG["port"]
        self.connection = None
    
    def connect(self):
        """Kết nối đến MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if self.connection.is_connected():
                print(f"Kết nối thành công đến MySQL (port {self.port})")
                return True
        except Error as e:
            print(f"Lỗi kết nối: {e}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Đã ngắt kết nối MySQL")
    
    def execute_query(self, query, params=None):
        """Thực thi query (INSERT, UPDATE, DELETE)"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Lỗi thực thi query: {e}")
            return None
    
    def fetch_one(self, query, params=None):
        """Lấy 1 bản ghi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            print(f"Lỗi fetch_one: {e}")
            return None
    
    def fetch_all(self, query, params=None):
        """Lấy tất cả bản ghi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi fetch_all: {e}")
            return []

def get_connection():
    """
    Hàm tiện ích cho các module khác (vd: face_routes)
    """
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"]
        )
        return conn
    except Error as e:
        print(f"❌ Không thể kết nối MySQL: {e}")
        return None
def init_database():
    """
    Kiểm tra kết nối database - KHÔNG TẠO BẢNG MỚI
    Database đã được tạo từ file SQL
    """
    try:
        # Kết nối để kiểm tra
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = connection.cursor()
        
        # Kiểm tra database tồn tại
        cursor.execute("SHOW DATABASES LIKE 'python_project'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Database 'python_project' đã tồn tại")
            
            # Kiểm tra các bảng cần thiết
            cursor.execute("USE python_project")
            
            tables_to_check = [
                'student', 'student_embeddings', 'attendance', 
                'class', 'login', 'major', 'shift', 'study', 'type'
            ]
            
            print("\n📋 Kiểm tra các bảng:")
            for table in tables_to_check:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    print(f"  ✅ Bảng '{table}' đã tồn tại")
                else:
                    print(f"  ❌ Bảng '{table}' CHƯA tồn tại")
            
            print("\n✅ Kết nối database thành công!")
        else:
            print("❌ Database 'python_project' chưa tồn tại!")
            print("📝 Vui lòng import file SQL vào phpMyAdmin trước.")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print("💡 Hãy đảm bảo XAMPP MySQL đang chạy và import file SQL.")

if __name__ == "__main__":
    init_database()
