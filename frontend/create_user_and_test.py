import requests
import json
import base64
from io import BytesIO
from PIL import Image

# Backend URL configuration
BACKEND_URL = "https://pac-hbbnehbxy-adole007s-projects.vercel.app"
API_URL = f"{BACKEND_URL}/api"

def create_test_user():
    """Create a test user"""
    user_data = {
        "username": "admin",
        "email": "admin@jajuwa.com",
        "full_name": "Admin User",
        "password": "password",
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        print(f"User creation status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ User created successfully!")
            return True
        else:
            print(f"User creation failed: {response.text}")
            # If user already exists, that's fine
            if "already registered" in response.text.lower():
                print("User already exists, continuing...")
                return True
            return False
            
    except Exception as e:
        print(f"User creation error: {e}")
        return False

def perform_login():
    """Try to login with the test user"""
    login_data = {
        "username": "admin",
        "password": "password"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Login successful!")
            return data.get('access_token')
        else:
            print(f"✗ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def get_all_patients(token):
    """Get all patients from the system"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/patients", headers=headers)
        print(f"Get patients status: {response.status_code}")
        
        if response.status_code == 200:
            patients = response.json()
            print(f"Found {len(patients)} patients")
            return patients
        else:
            print(f"Failed to get patients: {response.text}")
            return []
            
    except Exception as e:
        print(f"Error getting patients: {e}")
        return []

def analyze_patient_images(token, patient):
    """Analyze images for a specific patient"""
    headers = {"Authorization": f"Bearer {token}"}
    patient_id = patient['id']
    patient_name = f"{patient['first_name']} {patient['last_name']}"
    
    print(f"\n=== Analyzing images for {patient_name} (ID: {patient_id}) ===")
    
    try:
        response = requests.get(f"{API_URL}/patients/{patient_id}/images", headers=headers)
        print(f"Get images status: {response.status_code}")
        
        if response.status_code == 200:
            images = response.json()
            print(f"Found {len(images)} images")
            
            if not images:
                print("No images to analyze")
                return
            
            for i, image in enumerate(images, 1):
                print(f"\n--- Image {i} ---")
                print(f"ID: {image['id']}")
                print(f"Filename: {image.get('original_filename', 'N/A')}")
                print(f"Format: {image.get('image_format', 'N/A')}")
                print(f"Modality: {image.get('modality', 'N/A')}")
                print(f"Body Part: {image.get('body_part', 'N/A')}")
                print(f"File Size: {image.get('file_size', 0):,} bytes")
                
                # Check if this is a large DICOM file
                if image.get('image_format') == 'DICOM' and image.get('file_size', 0) > 100000:
                    print("🔍 This is a large DICOM file - potential issue candidate!")
                
                # Test the image endpoints
                test_image_endpoints(token, image)
                
                # Test base64 data
                test_base64_data(image)
                
        else:
            print(f"Failed to get images: {response.text}")
            
    except Exception as e:
        print(f"Error analyzing patient images: {e}")

def test_image_endpoints(token, image):
    """Test the image data and thumbnail endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    image_id = image['id']
    image_format = image.get('image_format', 'Unknown')
    
    print(f"Testing endpoints for {image_format} image...")
    
    # Test image data endpoint
    try:
        response = requests.get(f"{API_URL}/images/{image_id}/data", headers=headers)
        print(f"  Image data endpoint: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'unknown')
            data_size = len(response.content)
            print(f"  Content-Type: {content_type}")
            print(f"  Data size: {data_size:,} bytes")
            
            # Try to process as image if it's PNG format (converted DICOM)
            if 'png' in content_type.lower():
                try:
                    img = Image.open(BytesIO(response.content))
                    print(f"  ✓ Image loaded successfully: {img.size}, mode: {img.mode}")
                except Exception as e:
                    print(f"  ✗ Failed to load as image: {e}")
            elif 'dicom' in content_type.lower() or 'application/dicom' in content_type.lower():
                print(f"  ⚠️  DICOM format detected - frontend may have issues loading this!")
            
        else:
            print(f"  ✗ Failed: {response.text}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Test thumbnail endpoint
    try:
        response = requests.get(f"{API_URL}/images/{image_id}/thumbnail", headers=headers)
        print(f"  Thumbnail endpoint: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'unknown')
            data_size = len(response.content)
            print(f"  Thumbnail Content-Type: {content_type}")
            print(f"  Thumbnail size: {data_size:,} bytes")
            
            try:
                img = Image.open(BytesIO(response.content))
                print(f"  ✓ Thumbnail loaded successfully: {img.size}, mode: {img.mode}")
            except Exception as e:
                print(f"  ✗ Failed to load thumbnail: {e}")
                
        else:
            print(f"  ✗ Thumbnail failed: {response.text}")
            
    except Exception as e:
        print(f"  ✗ Thumbnail error: {e}")

def test_base64_data(image):
    """Test the base64 image data stored in the database"""
    print(f"Testing base64 data...")
    
    # Test main image data
    image_data = image.get('image_data')
    if image_data:
        try:
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))
            print(f"  ✓ Base64 image data valid: {img.size}, mode: {img.mode}")
            print(f"  Base64 data size: {len(img_bytes):,} bytes")
        except Exception as e:
            print(f"  ✗ Base64 image data invalid: {e}")
            print(f"  Base64 string length: {len(image_data) if image_data else 0}")
    else:
        print(f"  ✗ No base64 image data found")
    
    # Test thumbnail data
    thumbnail_data = image.get('thumbnail_data')
    if thumbnail_data:
        try:
            thumb_bytes = base64.b64decode(thumbnail_data)
            thumb = Image.open(BytesIO(thumb_bytes))
            print(f"  ✓ Base64 thumbnail data valid: {thumb.size}, mode: {thumb.mode}")
            print(f"  Base64 thumbnail size: {len(thumb_bytes):,} bytes")
        except Exception as e:
            print(f"  ✗ Base64 thumbnail data invalid: {e}")
            print(f"  Base64 thumbnail string length: {len(thumbnail_data) if thumbnail_data else 0}")
    else:
        print(f"  ✗ No base64 thumbnail data found")

def main():
    print("=== PAC System DICOM Issue Diagnosis ===")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Step 1: Create test user
    print("\n1. Creating test user...")
    if not create_test_user():
        print("✗ Could not create test user")
    
    # Step 2: Try to login
    print("\n2. Attempting login...")
    token = perform_login()
    
    if not token:
        print("✗ Could not login. Exiting.")
        return
    
    print(f"✓ Login successful, token obtained")
    
    # Step 3: Get all patients
    print("\n3. Getting patients...")
    patients = get_all_patients(token)
    
    if not patients:
        print("✗ No patients found or could not retrieve patients")
        return
    
    # Step 4: Analyze each patient's images
    print("\n4. Analyzing patient images...")
    
    for patient in patients:
        analyze_patient_images(token, patient)
    
    print("\n=== Analysis Complete ===")
    print("\nLook for images marked with 🔍 - these are likely causing the DICOM loading issues!")

if __name__ == "__main__":
    main()
