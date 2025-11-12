"""
API Client - Functions to call backend API
"""
import requests
import streamlit as st

# API Base URL
API_URL = "http://localhost:8000"


def get_auth_header():
    """Lấy authorization header từ session state"""
    token = st.session_state.get('token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ==================== Authentication ====================

def login_teacher(email=None, phone=None, password=None):
    """Đăng nhập giảng viên"""
    data = {"password": password}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    
    try:
        response = requests.post(f"{API_URL}/api/auth/login", data=data)
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Lỗi kết nối: {str(e)}"}


def register_teacher(name, email, phone, password):
    """Đăng ký giảng viên"""
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password
    }
    try:
        url = f"{API_URL}/api/auth/register"
        print(f"Calling API: {url}")
        print(f"Data: {data}")
        response = requests.post(url, data=data)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"success": False, "message": f"Lỗi kết nối: {str(e)}"}
    except Exception as e:
        print(f"Other error: {str(e)}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}


def verify_token(token):
    """Xác thực token"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/api/auth/verify", headers=headers)
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Lỗi kết nối: {str(e)}"}


def get_teacher_classes(teacher_id):
    """Lấy danh sách lớp của giảng viên"""
    try:
        headers = get_auth_header()
        response = requests.get(f"{API_URL}/api/auth/classes/{teacher_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"total": 0, "classes": []}

# ==================== Statistics ====================

def get_statistics():
    """Lấy thống kê tổng quan"""
    response = requests.get(f"{API_URL}/api/stats")
    response.raise_for_status()
    return response.json()

# ==================== Attendance ====================

def check_attendance(image, class_id, attendance_date=None):
    """Điểm danh"""
    files = {"image": image.getvalue()}
    data = {"class_id": class_id}
    if attendance_date:
        data["date"] = attendance_date
    response = requests.post(f"{API_URL}/api/attendance/checkin", files=files, data=data)
    return response

def get_class_attendance_today(class_id):
    """Lấy danh sách điểm danh của lớp hôm nay"""
    response = requests.get(f"{API_URL}/api/attendance/class/{class_id}/today")
    response.raise_for_status()
    return response.json()
