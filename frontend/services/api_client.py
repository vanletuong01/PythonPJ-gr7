import requests
API_BASE_URL = "http://localhost:8000/api/v1"

def register(data):
    return requests.post(f"{API_BASE_URL}/auth/register", json=data)

def login(data):
    return requests.post(f"{API_BASE_URL}/auth/login", json=data)