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


def create_student(payload: dict, uploaded_file=None):
    """
    Tạo sinh viên mới – gửi dữ liệu + ảnh (nếu có) xuống backend.
    """
    url = f"{API_BASE}/student/create"

    try:
        # Nếu có file ảnh
        if uploaded_file is not None:
            files = {
                "StudentPhoto": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }
            resp = requests.post(url, data=payload, files=files, timeout=TIMEOUT)
        else:
            resp = requests.post(url, json=payload, timeout=TIMEOUT)

        return _safe_json(resp)

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
    
def get_classes_by_teacher(id_login):
    try:
        resp = requests.get(f"{API_BASE}/class/by_teacher/{id_login}")
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []
