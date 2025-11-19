import os
import requests

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api/v1")
TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

def _safe_json(resp):
    try:
        return resp.json()
    except:
        return {"success": False, "message": resp.text or f"HTTP {resp.status_code}"}

def register_teacher(email: str, password: str, name: str):
    url = f"{API_BASE}/auth/register"
    payload = {"email": email, "password": password, "name": name}
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        data = _safe_json(resp)
        data.setdefault("status", resp.status_code)
        data.setdefault("url", url)
        return data
    except Exception as e:
        return {"success": False, "message": str(e), "status": 0}

def login_teacher(email: str, password: str):
    url = f"{API_BASE}/auth/login"
    payload = {"email": email, "password": password}
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        data = _safe_json(resp)
        data.setdefault("status", resp.status_code)
        return data
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_majors():
    try:
        resp = requests.get(f"{API_BASE}/class/majors", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_types():
    try:
        resp = requests.get(f"{API_BASE}/class/types", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_shifts():
    try:
        resp = requests.get(f"{API_BASE}/class/shifts", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_classes():
    try:
        resp = requests.get(f"{API_BASE}/class/list", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_dashboard_stats():
    try:
        resp = requests.get(f"{API_BASE}/class/dashboard/stats", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def create_class(data: dict):
    url = f"{API_BASE}/class/create"
    print(f"[DEBUG] create_class calling {url}")
    try:
        resp = requests.post(url, json=data, timeout=TIMEOUT)
        return resp
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] ConnectionError: {e}")
        class MockResp:
            status_code = 0
            text = "Không kết nối được backend"
        return MockResp()
    except Exception as e:
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
        # SỬA: Đổi "/class/" thành "/student/" vì API này nằm bên student_api.py
        url = f"{API_BASE}/student/students_in_class/{class_id}"
        
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        else:
            # In ra lỗi để debug nếu không phải 200
            print(f"[DEBUG API] Error fetching students: {resp.status_code} - {resp.text}")
            return []
    except Exception as e:
        print(f"[DEBUG API] Exception: {e}")
        return []

def get_attendance_by_date(class_id):
    try:
        resp = requests.get(f"{API_BASE}/class/attendance_by_date/{class_id}", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def handle_response(res):
    try:
        res.raise_for_status()
        return res.json()
    except requests.HTTPError as e:
        print(f"API Error {res.status_code}: {res.text}")
        raise e

def create_student(data: dict):
    url = f"{API_BASE}/student/add"
    res = requests.post(url, json=data, timeout=TIMEOUT)
    return handle_response(res)

def search_students(keyword: str, limit: int = 30):
    url = f"{API_BASE}/student/search"
    params = {"q": keyword, "limit": limit}
    res = requests.get(url, params=params, timeout=TIMEOUT)
    return handle_response(res)

async def assign_student_to_class(student_id, class_id):
    url = f"{BASE_URL}/class/assign"
    payload = {
        "student_id": student_id,
        "class_id": class_id
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

    """
    Gán sinh viên vào lớp.
    payload ví dụ: {"ClassID": 123, "StudentCode": "2331500001"}
    """
    url = f"{API_BASE}/class/assign"    # dùng API_BASE chứ không phải BASE_URL
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        # trả về JSON hoặc mock nếu backend trả kiểu khác
        try:
            return resp.json()
        except:
            return {"success": True, "status": resp.status_code, "text": resp.text}
    except requests.exceptions.HTTPError as e:
        # in debug để dễ thấy lỗi từ backend
        print(f"[API ERROR] assign_student_to_class {resp.status_code}: {resp.text}")
        raise
    except requests.exceptions.ConnectionError as e:
        print(f"[API ERROR] ConnectionError assign_student_to_class: {e}")
        return {"success": False, "message": "Không kết nối được backend", "status": 0}
    except Exception as e:
        print(f"[API ERROR] assign_student_to_class: {e}")
        return {"success": False, "message": str(e), "status": 0}

def get_student_attendance(class_id, student_id):
    """
    Lấy lịch sử điểm danh của sinh viên (Mock hoặc gọi API thật)
    """
    # URL này phải khớp với backend của bạn
    url = f"{API_BASE}/attendance/history/{class_id}/{student_id}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def get_student_detail(student_id):
    url = f"http://127.0.0.1:8000/api/v1/student/detail/{student_id}"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        if data.get("success"):
            return data["data"]
    return None
