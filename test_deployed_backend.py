#!/usr/bin/env python3
"""
Test the deployed backend API on Vercel
"""

import requests
import json

def test_deployed_backend():
    """Test the deployed backend API"""
    base_url = "https://jajuwa-healthcare-r8vx8v3z6-adole007s-projects.vercel.app"
    
    print("Testing deployed backend API...")
    print(f"Base URL: {base_url}")
    
    # Test the root endpoint
    try:
        print("\n1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Root endpoint working!")
        else:
            print(f"❌ Root endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test the health endpoint
    try:
        print("\n2. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working!")
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test login endpoint
    try:
        print("\n3. Testing login endpoint...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login endpoint working!")
            print(f"User: {data.get('user', {}).get('username')} - {data.get('user', {}).get('role')}")
            print(f"Token: {data.get('access_token', '')[:50]}...")
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")

if __name__ == "__main__":
    test_deployed_backend()
