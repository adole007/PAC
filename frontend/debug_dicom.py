import requests
import json
import base64
from io import BytesIO
from PIL import Image
import os

# Configuration
BACKEND_URL = "https://pac-hbbnehbxy-adole007s-projects.vercel.app"
API_URL = f"{BACKEND_URL}/api"

def test_backend_login():
    """Test backend login"""
    login_data = {
        "username": "admin",
        "password": "password"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_get_patients(token):
    """Get all patients"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/patients", headers=headers)
        print(f"Get patients status: {response.status_code}")
        
        if response.status_code == 200:
            patients = response.json()
            print(f"Found {len(patients)} patients")
            return patients
        else:
            print(f"Get patients failed: {response.text}")
            return []
            
    except Exception as e:
        print(f"Get patients error: {e}")
        return []

def test_get_patient_images(token, patient_id):
    """Get images for a specific patient"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/patients/{patient_id}/images", headers=headers)
        print(f"Get patient images status: {response.status_code}")
        
        if response.status_code == 200:
            images = response.json()
            print(f"Found {len(images)} images for patient {patient_id}")
            return images
        else:
            print(f"Get patient images failed: {response.text}")
            return []
            
    except Exception as e:
        print(f"Get patient images error: {e}")
        return []

def test_image_endpoints(token, image_id, image_format):
    """Test the image data and thumbnail endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nTesting image {image_id} (format: {image_format})")
    
    # Test image data endpoint
    try:
        response = requests.get(f"{API_URL}/images/{image_id}/data", headers=headers)
        print(f"Image data endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Image data content-type: {response.headers.get('content-type')}")
            print(f"Image data size: {len(response.content)} bytes")
            
            # Try to open as image if it's not DICOM
            if image_format != 'DICOM':
                try:
                    img = Image.open(BytesIO(response.content))
                    print(f"Image opened successfully: {img.size}, mode: {img.mode}")
                except Exception as e:
                    print(f"Failed to open image: {e}")
        else:
            print(f"Image data endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"Image data endpoint error: {e}")
    
    # Test thumbnail endpoint
    try:
        response = requests.get(f"{API_URL}/images/{image_id}/thumbnail", headers=headers)
        print(f"Thumbnail endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Thumbnail content-type: {response.headers.get('content-type')}")
            print(f"Thumbnail size: {len(response.content)} bytes")
            
            try:
                img = Image.open(BytesIO(response.content))
                print(f"Thumbnail opened successfully: {img.size}, mode: {img.mode}")
            except Exception as e:
                print(f"Failed to open thumbnail: {e}")
        else:
            print(f"Thumbnail endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"Thumbnail endpoint error: {e}")

def test_base64_fallback(token, image_id):
    """Test if base64 fallback works"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/images/{image_id}", headers=headers)
        print(f"Get image metadata status: {response.status_code}")
        
        if response.status_code == 200:
            image_data = response.json()
            
            # Test base64 image data
            if image_data.get('image_data'):
                try:
                    img_bytes = base64.b64decode(image_data['image_data'])
                    img = Image.open(BytesIO(img_bytes))
                    print(f"Base64 image opened successfully: {img.size}, mode: {img.mode}")
                except Exception as e:
                    print(f"Failed to open base64 image: {e}")
            
            # Test base64 thumbnail
            if image_data.get('thumbnail_data'):
                try:
                    thumb_bytes = base64.b64decode(image_data['thumbnail_data'])
                    thumb = Image.open(BytesIO(thumb_bytes))
                    print(f"Base64 thumbnail opened successfully: {thumb.size}, mode: {thumb.mode}")
                except Exception as e:
                    print(f"Failed to open base64 thumbnail: {e}")
                    
        else:
            print(f"Get image metadata failed: {response.text}")
            
    except Exception as e:
        print(f"Get image metadata error: {e}")

def main():
    print("=== PAC System DICOM Debug Test ===")
    
    # Step 1: Login
    token = test_backend_login()
    if not token:
        print("Failed to login. Exiting.")
        return
    
    # Step 2: Get patients
    patients = test_get_patients(token)
    if not patients:
        print("No patients found. Exiting.")
        return
    
    # Step 3: Test each patient's images
    for patient in patients:
        print(f"\n=== Patient: {patient['first_name']} {patient['last_name']} ===")
        images = test_get_patient_images(token, patient['id'])
        
        if not images:
            print("No images found for this patient.")
            continue
        
        # Test each image
        for image in images:
            print(f"\nImage ID: {image['id']}")
            print(f"Filename: {image['original_filename']}")
            print(f"Format: {image['image_format']}")
            print(f"Modality: {image['modality']}")
            print(f"Body part: {image['body_part']}")
            
            # Test endpoints
            test_image_endpoints(token, image['id'], image['image_format'])
            
            # Test base64 fallback
            test_base64_fallback(token, image['id'])
            
            print("-" * 50)

if __name__ == "__main__":
    main()
