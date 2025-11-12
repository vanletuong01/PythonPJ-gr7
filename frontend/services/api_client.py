import streamlit as st
import requests
API_BASE_URL = "http://localhost:8000/api/v1"

def login_teacher(email, password):
    resp = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    try:
        data = resp.json()
    except Exception:
        data = {}
    if resp.status_code == 200:
        return {
            "success": True,
            "token": data.get("access_token"),
            "user": data.get("user")
        }
    else:
        return {
            "success": False,
            "message": data.get("detail", "Đăng nhập thất bại")
        }
def register_teacher(email, password, name, phone=""):
    resp = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "phone": phone
        }
    )
    try:
        data = resp.json()
    except Exception:
        data = {}
    print("REGISTER RESPONSE:", resp.status_code, data)

    if resp.status_code == 200:
        return {"success": True, "user": data}
    else:
        return {"success": False, "message": data.get("detail", "Đăng ký thất bại")}
def create_class(data):
    resp = requests.post(f"{API_BASE_URL}/class/create", json=data)
    return resp
def get_majors():
    resp = requests.get(f"{API_BASE_URL}/class/majors")
    try:
        return resp.json()
    except Exception:
        st.error("Không lấy được dữ liệu chuyên ngành. Kiểm tra backend hoặc API.")
        return []

def get_types():
    resp = requests.get(f"{API_BASE_URL}/class/types")
    try:
        return resp.json()
    except Exception:
        st.error("Không lấy được dữ liệu loại lớp. Kiểm tra backend hoặc API.")
        return []

def get_shifts():
    resp = requests.get(f"{API_BASE_URL}/class/shifts")
    try:
        return resp.json()
    except Exception:
        st.error("Không lấy được dữ liệu ca học. Kiểm tra backend hoặc API.")
        return []