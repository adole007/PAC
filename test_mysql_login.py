#!/usr/bin/env python3
"""
Test MySQL backend login functionality
"""

import requests
import json

def test_mysql_backend():
    """Test MySQL backend API login"""
    backend_url = "http://localhost:8001"
    
    # Test health endpoint
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
            print(f"   Users: {health_data.get('users')}")
            print(f"   Config: {health_data.get('config')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not reachable: {e}")
        print("   Make sure to run: python backend/server_mysql.py")
        return False
    
    # Test admin login
    print("\nTesting admin login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Admin login successful!")
            print(f"   Token: {token_data['access_token'][:50]}...")
            print(f"   User: {token_data['user']['username']} - {token_data['user']['role']}")
            
            # Test clinician login
            print("\nTesting clinician login...")
            clinician_data = {
                "username": "clinician",
                "password": "admin123"
            }
            
            response = requests.post(f"{backend_url}/api/auth/login", json=clinician_data, timeout=5)
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Clinician login successful!")
                print(f"   User: {token_data['user']['username']} - {token_data['user']['role']}")
                return True
            else:
                print(f"❌ Clinician login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing MySQL Backend Login...")
    print("=" * 40)
    
    success = test_mysql_backend()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed!")
        print("\nYou can now login to the frontend with:")
        print("Username: admin (or clinician)")
        print("Password: admin123")
    else:
        print("❌ Tests failed!")
        print("Make sure the MySQL backend is running:")
        print("python backend/server_mysql.py")
