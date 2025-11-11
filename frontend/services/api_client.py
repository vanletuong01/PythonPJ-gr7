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
            "message": data.get("detail", "Login failed")
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
    if resp.status_code == 200:
        return {"success": True, "user": data}
    else:
        return {"success": False, "message": data.get("detail", "Đăng ký thất bại")}