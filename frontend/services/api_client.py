import requests

API_BASE_URL = "http://localhost:8000/api/v1"

def get_majors():
    try:
        r = requests.get(f"{API_BASE_URL}/class/majors", timeout=5)
        return r.json() if r.ok else []
    except Exception:
        return []

def get_types():
    try:
        r = requests.get(f"{API_BASE_URL}/class/types", timeout=5)
        return r.json() if r.ok else []
    except Exception:
        return []

def get_shifts():
    try:
        r = requests.get(f"{API_BASE_URL}/class/shifts", timeout=5)
        return r.json() if r.ok else []
    except Exception:
        return []

def create_class(data):
    try:
        r = requests.post(f"{API_BASE_URL}/class/create", json=data, timeout=10)
        return r
    except Exception:
        return None