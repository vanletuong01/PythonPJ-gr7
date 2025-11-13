import os
import requests
import zipfile
import subprocess
import threading
import time
import sys

def download_and_extract_ngrok():
    """Tải và giải nén ngrok hoàn toàn tự động"""
    ngrok_exe = "ngrok.exe"
    ngrok_zip = "ngrok.zip"
    
    # Nếu đã có ngrok.exe thì không cần tải lại
    if os.path.exists(ngrok_exe):
        print("ngrok.exe already exists")
        return True
    
    print("📥 Downloading ngrok...")
    
    try:
        # URL tải ngrok chính thức
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        
        # Tải file với timeout
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Lưu file zip
        with open(ngrok_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print("✅ Download completed, extracting...")
        
        # Giải nén
        with zipfile.ZipFile(ngrok_zip, 'r') as zip_ref:
            zip_ref.extractall()
        
        # Xóa file zip
        os.remove(ngrok_zip)
        
        # Kiểm tra ngrok.exe đã được giải nén
        if os.path.exists(ngrok_exe):
            print("✅ ngrok.exe ready to use!")
            return True
        else:
            print("❌ ngrok.exe not found after extraction")
            return False
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Xóa file lỗi nếu có
        if os.path.exists(ngrok_zip):
            os.remove(ngrok_zip)
        return False

def setup_ngrok_auth():
    """Thiết lập auth token cho ngrok"""
    auth_token = "35OTfUFjtX3OCiLvyI5cWiRGDv3_2mxFY73n2jLX8MK2e2ckA"  # THAY BẰNG TOKEN THẬT CỦA BẠN
    
    if not auth_token or auth_token == "35OTfUFjtX3OCiLvyI5cWiRGDv3_2mxFY73n2jLX8MK2e2ckA":
        print("⚠️  Please add your ngrok auth token to the code!")
        return False
    
    try:
        # Chạy lệnh thêm auth token
        command = f'ngrok config add-authtoken {auth_token}'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Auth token configured")
            return True
        else:
            print(f"❌ Auth setup failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Auth setup error: {e}")
        return False

def start_ngrok_tunnel(port, name):
    """Khởi chạy ngrok tunnel"""
    print(f"🚀 Starting {name} on port {port}...")
    
    try:
        # Chạy ngrok
        command = f'ngrok http {port} --log=stdout'
        process = subprocess.Popen(command, shell=True)
        
        # Đợi ngrok khởi động
        time.sleep(5)
        
        # Lấy URL từ API
        max_retries = 3
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    for tunnel in tunnels:
                        if str(port) in tunnel["config"]["addr"]:
                            url = tunnel["public_url"]
                            print(f"✅ {name} URL: {url}")
                            return url, process
                time.sleep(2)
            except:
                if i < max_retries - 1:
                    time.sleep(2)
                    continue
        
        print(f"⚠️  Could not get {name} URL after retries")
        return None, process
        
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None, None

def start_backend():
    """Chạy FastAPI backend"""
    try:
        print("🔧 Starting FastAPI backend...")
        subprocess.run(["uvicorn", "backend.app.main:app", "--reload", "--port", "8000"])
    except Exception as e:
        print(f"❌ Backend error: {e}")

def start_frontend():
    """Chạy Streamlit frontend"""
    try:
        print("🎨 Starting Streamlit frontend...")
        subprocess.run(["streamlit", "run", "frontend/app.py", "--server.port", "8801"])
    except Exception as e:
        print(f"❌ Frontend error: {e}")

def update_frontend_config(backend_url):
    """Cập nhật backend URL trong frontend"""
    try:
        frontend_file = "frontend/services/api_client.py"
        if os.path.exists(frontend_file):
            with open(frontend_file, "r", encoding="utf-8") as f:
                content = f.read()
            # Thay thế API_BASE_URL
            import re
            new_content = re.sub(
                r'API_BASE_URL\s*=\s*".*?"',
                f'API_BASE_URL = "{backend_url}/api/v1"',
                content
            )
            with open(frontend_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Updated frontend with backend URL: {backend_url}/api/v1")
    except Exception as e:
        print(f"⚠️  Could not update frontend config: {e}")

def main():
    print("🎯 AUTO DEPLOYMENT STARTING...")
    if not download_and_extract_ngrok():
        print("❌ Cannot continue without ngrok")
        return
    if not setup_ngrok_auth():
        print("⚠️  Continuing without auth token (limited functionality)")
    backend_thread = threading.Thread(target=start_backend)
    frontend_thread = threading.Thread(target=start_frontend)
    backend_thread.daemon = True
    frontend_thread.daemon = True
    backend_thread.start()
    frontend_thread.start()
    print("⏳ Waiting for servers to start...")
    time.sleep(15)
    # Chỉ mở tunel cho frontend
    frontend_url, frontend_process = start_ngrok_tunnel(8801, "Frontend")
    print("\n" + "="*50)
    print("🎊 DEPLOYMENT COMPLETED!")
    print("="*50)
    if frontend_url:
        print(f"🌐 Frontend App: {frontend_url}")
        print(f"\n📤 SHARE THIS WITH OTHERS: {frontend_url}")
    print("\n⏳ Press Ctrl+C to stop all services...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        if frontend_process:
            frontend_process.terminate()
        print("✅ All services stopped")