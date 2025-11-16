import requests
from requests import Response

API_BASE = "http://127.0.0.1:8000/api/v1"


# -----------------------
# Helper xử lý request
# -----------------------
def handle_response(res: Response):
    try:
        res.raise_for_status()
        return res.json()
    except requests.HTTPError as e:
        print(f"❌ API Error {res.status_code}: {res.text}")
        raise e


# -----------------------
# STUDENT API
# -----------------------
def get_students():
    url = f"{API_BASE}/student/"
    res = requests.get(url, timeout=10)
    return handle_response(res)


def search_students(keyword: str, limit: int = 30):
    url = f"{API_BASE}/student/search"
    params = {"q": keyword, "limit": limit}
    res = requests.get(url, params=params, timeout=10)
    return handle_response(res)


def get_student_by_id(student_id: int):
    url = f"{API_BASE}/student/{student_id}"
    res = requests.get(url, timeout=10)
    return handle_response(res)


def create_student(data: dict):
    url = f"{API_BASE}/student/"
    res = requests.post(url, json=data, timeout=10)
    return handle_response(res)


def update_student(student_id: int, data: dict):
    url = f"{API_BASE}/student/{student_id}"
    res = requests.put(url, json=data, timeout=10)
    return handle_response(res)


def delete_student(student_id: int):
    url = f"{API_BASE}/student/{student_id}"
    res = requests.delete(url, timeout=10)
    return handle_response(res)


# -----------------------
# CLASS API
# -----------------------
def get_classes():
    url = f"{API_BASE}/class/"
    res = requests.get(url, timeout=10)
    return handle_response(res)


def create_class(data: dict):
    url = f"{API_BASE}/class/"
    res = requests.post(url, json=data, timeout=10)
    return handle_response(res)


# -----------------------
# SUBJECT API
# -----------------------
def get_subjects():
    url = f"{API_BASE}/subject/"
    res = requests.get(url, timeout=10)
    return handle_response(res)


def create_subject(data: dict):
    url = f"{API_BASE}/subject/"
    res = requests.post(url, json=data, timeout=10)
    return handle_response(res)

# -----------------------
# MAJOR API (ngành học)
# -----------------------
def get_majors():
    url = f"{API_BASE}/major/"
    res = requests.get(url, timeout=10)
    return handle_response(res)


# -----------------------
# TYPE API (loại sinh viên hoặc loại đối tượng)
# -----------------------
def get_types():
    url = f"{API_BASE}/type/"
    res = requests.get(url, timeout=10)
    return handle_response(res)
def login_teacher(email: str, password: str):
    url = f"{API_BASE}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    res = requests.post(url, json=payload, timeout=10)
    return handle_response(res)


# -----------------------
# DASHBOARD API
# -----------------------
def get_dashboard_stats():
    url = f"{API_BASE}/dashboard/stats"
    try:
        res = requests.get(url, timeout=10)
        return handle_response(res)
    except Exception as e:
<<<<<<< HEAD
        print(f"[ERROR] create_class: {e!r}")
        class MockResp:
            status_code = 0
            text = str(e)
        return MockResp()
    
def get_classes_by_teacher(id_login):
    try:
        resp = requests.get(f"{API_BASE}/class/by_teacher/{id_login}")
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []
    
def get_students_in_class(class_id):
    try:
        resp = requests.get(f"{API_BASE}/class/students_in_class/{class_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_attendance_by_date(class_id):
    try:
        resp = requests.get(f"{API_BASE}/class/attendance_by_date/{class_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []
    
def get_attendance_by_date(class_id):
    try:
        resp = requests.get(f"{API_BASE}/class/attendance_by_date/{class_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []
=======
        print("❌ Lỗi get_dashboard_stats:", e)
        return {}
>>>>>>> e660665db4b78d84c712b369d61b71444ed75c46
