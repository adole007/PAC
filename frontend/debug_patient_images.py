#!/usr/bin/env python3

import requests
import json

# Configuration
BACKEND_URL = "https://pac-ik6nachlb-adole007s-projects.vercel.app"

def test_login():
    """Test login and get token"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful: {data['user']['username']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_get_patients(token):
    """Test getting patients"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/patients", headers=headers)
        
        if response.status_code == 200:
            patients = response.json()
            print(f"✅ Retrieved {len(patients)} patients")
            for patient in patients:
                print(f"  - {patient['first_name']} {patient['last_name']} (ID: {patient['id']})")
            return patients
        else:
            print(f"❌ Failed to get patients: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Get patients error: {e}")
        return []

def test_get_patient_images(token, patient_id):
    """Test getting patient images - the failing endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BACKEND_URL}/api/patients/{patient_id}/images"
        print(f"🔍 Testing URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Retrieved {len(images)} images for patient {patient_id}")
            for image in images:
                print(f"  - {image['original_filename']} ({image['image_format']})")
            return images
        else:
            print(f"❌ Failed to get images: {response.status_code}")
            print(f"Response content: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Get images error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("=== Debug Patient Images Endpoint ===")
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without valid token")
        return
    
    # Test get patients
    patients = test_get_patients(token)
    if not patients:
        print("❌ Cannot test images without patients")
        return
    
    # Test get images for each patient
    for patient in patients:
        print(f"\n🔍 Testing images for patient: {patient['first_name']} {patient['last_name']}")
        images = test_get_patient_images(token, patient['id'])
        
        if not images:
            print("⚠️  No images found for this patient")
        else:
            print(f"✅ Found {len(images)} images")

if __name__ == "__main__":
    main()
