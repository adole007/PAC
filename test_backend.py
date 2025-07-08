import requests
import json

# Test backend connection and create a test user
backend_url = "http://localhost:8001"

def test_backend_connection():
    try:
        response = requests.get(f"{backend_url}/docs")
        print(f"Backend connection: {'✓ SUCCESS' if response.status_code == 200 else '✗ FAILED'}")
        return response.status_code == 200
    except Exception as e:
        print(f"Backend connection: ✗ FAILED - {e}")
        return False

def create_test_user():
    user_data = {
        "username": "admin",
        "email": "admin@test.com",
        "full_name": "Test Admin",
        "password": "admin123",
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/auth/register", json=user_data)
        if response.status_code == 200:
            print("✓ Test user created successfully")
            print(f"Username: {user_data['username']}")
            print(f"Password: {user_data['password']}")
            return True
        else:
            print(f"✗ Failed to create user: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return False

def test_login():
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✓ Login test successful")
            token_data = response.json()
            print(f"Access token received: {token_data['access_token'][:50]}...")
            return True
        else:
            print(f"✗ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False

if __name__ == "__main__":
    print("Testing PAC Backend...")
    print("=" * 40)
    
    if test_backend_connection():
        create_test_user()
        test_login()
    else:
        print("\nMake sure the backend server is running:")
        print("cd backend && python server.py")
