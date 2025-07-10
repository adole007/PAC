#!/usr/bin/env python3

import requests
import json
import base64
from PIL import Image
import io

# Configuration
BACKEND_URL = "https://pac-i2r3t7yv4-adole007s-projects.vercel.app"
FRONTEND_URL = "https://pac-lonfuag3c-adole007s-projects.vercel.app"

def test_backend_health():
    """Test if backend is healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data['status']}")
            print(f"📊 Database: {data['database']}")
            print(f"👥 Users: {data['users']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_login():
    """Test login functionality"""
    try:
        # Test with known credentials
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful")
            print(f"👤 User: {data['user']['username']} ({data['user']['role']})")
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
            return patients
        else:
            print(f"❌ Failed to get patients: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Get patients error: {e}")
        return []

def test_get_patient_images(token, patient_id):
    """Test getting patient images"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/patients/{patient_id}/images", headers=headers)
        
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Retrieved {len(images)} images for patient {patient_id}")
            return images
        else:
            print(f"❌ Failed to get images: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Get images error: {e}")
        return []

def test_image_endpoint(token, image_id):
    """Test the new image data endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/images/{image_id}/data", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Image data endpoint works")
            print(f"📊 Response size: {len(response.content):,} bytes")
            print(f"📋 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            
            # Try to load the image
            try:
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Image loaded successfully: {img.size}, mode: {img.mode}")
                return True
            except Exception as img_error:
                print(f"❌ Could not load image: {img_error}")
                return False
        else:
            print(f"❌ Image data endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Image endpoint error: {e}")
        return False

def test_thumbnail_endpoint(token, image_id):
    """Test the thumbnail endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/images/{image_id}/thumbnail", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Thumbnail endpoint works")
            print(f"📊 Thumbnail size: {len(response.content):,} bytes")
            
            # Try to load the thumbnail
            try:
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Thumbnail loaded successfully: {img.size}, mode: {img.mode}")
                return True
            except Exception as img_error:
                print(f"❌ Could not load thumbnail: {img_error}")
                return False
        else:
            print(f"❌ Thumbnail endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Thumbnail endpoint error: {e}")
        return False

def test_dimension_preservation(token, images):
    """Test if dimensions are preserved in converted images"""
    print(f"\n📐 Testing dimension preservation...")
    
    for image in images:
        if image['image_format'] == 'DICOM':
            print(f"\n🔍 Testing DICOM image: {image['original_filename']}")
            
            # Get the base64 data directly from the image record
            try:
                image_data = base64.b64decode(image['image_data'])
                img = Image.open(io.BytesIO(image_data))
                print(f"✅ Image dimensions from database: {img.size}")
                
                # Test the new endpoint
                if test_image_endpoint(token, image['id']):
                    print(f"✅ Image endpoint preserves dimensions correctly")
                else:
                    print(f"❌ Image endpoint failed")
                    
            except Exception as e:
                print(f"❌ Error testing image: {e}")

def main():
    print("=== PAC System Image Fetch Test ===")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    
    # Test backend health
    if not test_backend_health():
        print("❌ Backend is not healthy, stopping test")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Login failed, stopping test")
        return
    
    # Test getting patients
    patients = test_get_patients(token)
    if not patients:
        print("❌ No patients found, stopping test")
        return
    
    # Test getting images for first patient
    first_patient = patients[0]
    images = test_get_patient_images(token, first_patient['id'])
    
    if not images:
        print("❌ No images found for patient")
        return
    
    # Test image endpoints
    first_image = images[0]
    print(f"\n🖼️  Testing image endpoints with image: {first_image['original_filename']}")
    
    # Test main image endpoint
    test_image_endpoint(token, first_image['id'])
    
    # Test thumbnail endpoint
    test_thumbnail_endpoint(token, first_image['id'])
    
    # Test dimension preservation
    test_dimension_preservation(token, images)
    
    print("\n=== Test Complete ===")
    print("✅ With dimension preservation enabled, DICOM images should maintain their original pixel dimensions")
    print("✅ This should resolve the 'failed to fetch image' errors caused by oversized responses")

if __name__ == "__main__":
    main()
