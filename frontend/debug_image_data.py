#!/usr/bin/env python3

import requests
import json
import base64
from PIL import Image
import io

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
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_image_data_endpoint(token, image_id):
    """Test the image data endpoint specifically"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BACKEND_URL}/api/images/{image_id}/data"
        print(f"🔍 Testing URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📏 Response Size: {len(response.content):,} bytes")
        
        if response.status_code == 200:
            # Try to load as image
            try:
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Image loaded successfully: {img.size}, mode: {img.mode}")
                return True
            except Exception as img_error:
                print(f"❌ Could not load image: {img_error}")
                return False
        else:
            print(f"❌ Failed to get image data: {response.status_code}")
            print(f"Response content: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Image data endpoint error: {e}")
        return False

def test_thumbnail_endpoint(token, image_id):
    """Test the thumbnail endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BACKEND_URL}/api/images/{image_id}/thumbnail"
        print(f"🔍 Testing thumbnail URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📊 Thumbnail Status Code: {response.status_code}")
        print(f"📏 Thumbnail Response Size: {len(response.content):,} bytes")
        
        if response.status_code == 200:
            # Try to load as image
            try:
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Thumbnail loaded successfully: {img.size}, mode: {img.mode}")
                return True
            except Exception as img_error:
                print(f"❌ Could not load thumbnail: {img_error}")
                return False
        else:
            print(f"❌ Failed to get thumbnail: {response.status_code}")
            print(f"Response content: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Thumbnail endpoint error: {e}")
        return False

def main():
    print("=== Debug Image Data Endpoints ===")
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without valid token")
        return
    
    # Get patients to find images
    headers = {"Authorization": f"Bearer {token}"}
    patients_response = requests.get(f"{BACKEND_URL}/api/patients", headers=headers)
    
    if patients_response.status_code == 200:
        patients = patients_response.json()
        print(f"✅ Found {len(patients)} patients")
        
        for patient in patients:
            print(f"\n🔍 Testing patient: {patient['first_name']} {patient['last_name']}")
            
            # Get images for this patient
            images_response = requests.get(f"{BACKEND_URL}/api/patients/{patient['id']}/images", headers=headers)
            
            if images_response.status_code == 200:
                images = images_response.json()
                print(f"✅ Found {len(images)} images")
                
                for image in images:
                    print(f"\n📱 Testing image: {image['original_filename']} ({image['image_format']})")
                    print(f"Image ID: {image['id']}")
                    
                    # Test image data endpoint
                    print("\n🖼️  Testing main image data endpoint:")
                    test_image_data_endpoint(token, image['id'])
                    
                    # Test thumbnail endpoint
                    print("\n🔍 Testing thumbnail endpoint:")
                    test_thumbnail_endpoint(token, image['id'])
                    
                    # Only test first image to avoid too much output
                    break
            else:
                print(f"❌ Failed to get images for patient: {images_response.status_code}")
    else:
        print(f"❌ Failed to get patients: {patients_response.status_code}")

if __name__ == "__main__":
    main()
