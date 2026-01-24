import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    for _ in range(10):
        try:
            requests.get(BASE_URL)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def test_api():
    if not wait_for_server():
        print("Server not up")
        return

    # 1. Create User
    user_data = {
        "username": "testuser",
        "password": "testpassword",
        "role": "admin"
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    print(f"Create User Status: {response.status_code}")
    if response.status_code not in [200, 400]: # 400 if exists
        print(f"Error creating user: {response.text}")
    
    # 2. Login
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Token received")
        
        # 3. Get Me
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        print(f"Get Me Status: {response.status_code}")
        print(f"User Data: {response.json()}")
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    test_api()
