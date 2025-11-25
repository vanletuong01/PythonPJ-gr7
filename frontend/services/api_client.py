import os
import requests

API_URL = os.getenv(
    "API_URL",
    "https://pythonpj-gr7.onrender.com/api/v1"
    )
TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

def _safe_json(resp):
    try:
        return resp.json()
    except:
        return {"success": False, "message": resp.text or f"HTTP {resp.status_code}"}

# --- CÁC HÀM CŨ CỦA BẠN (KHÔNG ĐỤNG VÀO) ---
def register_teacher(email: str, password: str, name: str):
    url = f"{API_URL}/auth/register"
    payload = {"email": email, "password": password, "name": name}
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        data = _safe_json(resp)
        data.setdefault("status", resp.status_code)
        return data
    except Exception as e:
        return {"success": False, "message": str(e), "status": 0}

def login_teacher(email: str, password: str):
    url = f"{API_URL}/auth/login"
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
        resp = requests.get(f"{API_URL}/class/majors", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_types():
    try:
        resp = requests.get(f"{API_URL}/class/types", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_shifts():
    try:
        resp = requests.get(f"{API_URL}/class/shifts", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_classes():
    try:
        resp = requests.get(f"{API_URL}/class/list", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_dashboard_stats():
    try:
        resp = requests.get(f"{API_URL}/class/dashboard/stats", timeout=TIMEOUT)
        return resp.json() if resp.status_code == 200 else {}
    except:
        return {}

def create_class(data: dict):
    url = f"{API_URL}/class/create"
    try:
        resp = requests.post(url, json=data, timeout=TIMEOUT)
        return resp
    except Exception as e:
        class MockResp:
            status_code = 0
            text = str(e)
        return MockResp()
    
def get_classes_by_teacher(teacher_id):
    """Lấy danh sách lớp học của giáo viên"""
    url = f"{API_URL}/class/by_teacher/{teacher_id}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        # In ra để debug (xóa sau khi test xong)
        print("🔍 [DEBUG] Classes from API:", data)
        
        return data
    except Exception as e:
        print(f"[API ERROR] get_classes_by_teacher: {e}")
        return []

    
# --- SỬA HÀM NÀY ĐỂ LOGGING LỖI ---
def get_students_in_class(class_id):
    try:
        url = f"{API_URL}/student/students_in_class/{class_id}"
        print(f"🔍 [API] Getting students for class {class_id}...") # Debug
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"⚠️ [API WARN] Get Students Failed: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ [API ERROR] Get Students: {e}")
        return []

def get_attendance_by_date(class_id):
    try:
        resp = requests.get(f"{API_URL}/class/attendance_by_date/{class_id}", timeout=TIMEOUT)
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

# --- SỬA HÀM NÀY ĐỂ LOGGING ---
def create_student(data: dict):
    url = f"{API_URL}/student/add"
    print(f"🚀 [API] Creating student: {data}") # Debug
    try:
        res = requests.post(url, json=data, timeout=TIMEOUT)
        return handle_response(res)
    except Exception as e:
        print(f"❌ [API ERROR] Create Student: {e}")
        return {"error": str(e)}

def search_students(keyword: str, limit: int = 30):
    url = f"{API_URL}/student/search"
    params = {"q": keyword, "limit": limit}
    try:
        res = requests.get(url, params=params, timeout=TIMEOUT)
        return handle_response(res)
    except:
        return []

def assign_student_to_class(student_id, class_id):
    """
    Gán sinh viên vào lớp.
    """
    url = f"{API_URL}/class/assign"
    
    # --- SỬA Ở ĐÂY: Đổi StudentID -> student_id, ClassID -> class_id ---
    payload = {
        "student_id": int(student_id),  # Chữ thường
        "class_id": int(class_id)       # Chữ thường
    }
    # -------------------------------------------------------------------
    
    print(f"🚀 [API] Assigning: {payload} -> {url}")

    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        
        # Nếu vẫn lỗi, in ra xem Server đòi cái gì
        if resp.status_code == 422:
            print(f"❌ CHI TIẾT LỖI 422: {resp.json()}")
            
        resp.raise_for_status()
        return resp.json()
        
    except Exception as e:
        print(f"❌ [API ERROR] Assign Failed: {e}")
        raise e
# --- CÁC HÀM KHÁC GIỮ NGUYÊN ---
def get_student_attendance(class_id, student_id):
    url = f"{API_URL}/attendance/history/{class_id}/{student_id}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def get_student_detail(student_id):
    url = f"{API_URL}/student/detail/{student_id}"
    try:
        resp = requests.get(url)
        if resp.ok:
            data = resp.json()
            if data.get("success"):
                return data["data"]
    except:
        pass
    return None


def get_attendance_session_detail(class_id, date):
    url = f"{API_URL}/attendance/session/{class_id}/{date}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        print(f"❌ [API ERROR] get_attendance_session_detail: {e}")
        return []
def get_session_detail(class_id, session_date):
    """
    Lấy chi tiết buổi học (danh sách SV đã/chưa điểm danh)
    session_date: format "YYYY-MM-DD" (VD: "2025-11-17")
    """
    url = f"{API_URL}/attendance/session-detail/{class_id}/{session_date}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ [API ERROR] get_session_detail: {e}")
        return {"success": False, "message": str(e)}

def manual_checkin(study_id: int, session_date: str):
    """
    Điểm danh thủ công
    
    Args:
        study_id: ID trong bảng study
        session_date: Ngày điểm danh (YYYY-MM-DD)
    """
    try:
        response = requests.post(
            f"{API_URL}/attendance/manual-checkin",
            params={
                "study_id": study_id,
                "session_date": session_date
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"[API ERROR] manual_checkin: {e}")
        return {"success": False, "message": str(e)}
    except Exception as e:
        print(f"[API ERROR] manual_checkin: {e}")
        return {"success": False, "message": str(e)}

def get_all_classes():
    url = f"{API_URL}/class/"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        print(f"❌ [API ERROR] get_all_classes: {e}")
        return []

def remove_student_from_class(class_id, student_id):
    url = f"{API_URL}/class/remove_student"
    try:
        resp = requests.post(url, json={"ClassID": class_id, "StudentID": student_id}, timeout=TIMEOUT)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ [API ERROR] remove_student_from_class: {e}")
        return False

def update_class(class_id, major_id, type_id, year, class_name):
    url = f"{API_URL}/class/update"
    data = {
        "ClassID": class_id,
        "MajorID": major_id,
        "TypeID": type_id,
        "DateStart": f"{year}-01-01",
        "ClassName": class_name
    }
    try:
        resp = requests.post(url, json=data, timeout=TIMEOUT)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ [API ERROR] update_class: {e}")
        return False



def update_student_info(student_id, full_name, default_class, birth_date, phone, cccd):
    url = f"{API_URL}/student/update" 
    data = {
        "StudentID": student_id,
        "FullName": full_name,
        "DefaultClass": default_class,
        "DateOfBirth": birth_date,
        "Phone": phone,
        "CitizenID": cccd
    }
    try:
        resp = requests.post(url, json=data, timeout=TIMEOUT)
        return resp.status_code == 200
    except Exception as e:
        print(f"[API ERROR] update_student_info: {e}")
        return False