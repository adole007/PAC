import requests
import json
import base64

# Test configuration
BASE_URL = "http://localhost:8000/api"
IMAGE_ID = "31ff7ae9-c97b-4d8e-948b-209f0d26c1d5"  # From our previous test

def get_auth_token():
    """Get authentication token"""
    # Use correct password
    credentials = [
        {"username": "clinician", "password": "admin123"},
        {"username": "admin", "password": "admin123"}
    ]
    
    for cred in credentials:
        response = requests.post(f"{BASE_URL}/auth/login", json=cred)
        if response.status_code == 200:
            print(f"✅ Logged in with {cred['username']}")
            return response.json()["access_token"]
        else:
            print(f"❌ Failed login with {cred['username']}: {response.status_code}")
    
    return None

def test_image_endpoint(token, image_id):
    """Test the image data endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing image endpoint for ID: {image_id}")
    
    # Test binary image data endpoint
    response = requests.get(f"{BASE_URL}/images/{image_id}/data", headers=headers)
    print(f"Binary image data response: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
    print(f"Content-Length: {response.headers.get('content-length', 'Not set')}")
    
    if response.status_code == 200:
        content = response.content
        print(f"First 10 bytes: {content[:10]}")
        
        if content.startswith(b'\x89PNG'):
            print("✅ Binary image is PNG format")
        elif content.startswith(b'\xff\xd8\xff'):
            print("✅ Binary image is JPEG format")
        else:
            print("⚠️  Unknown binary image format")
    else:
        print(f"❌ Failed to get binary image data: {response.text}")
    
    print("---")
    
    # Test base64 image data endpoint  
    response = requests.get(f"{BASE_URL}/images/{image_id}/data-base64", headers=headers)
    print(f"Base64 image data response: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✅ Base64 image data: format={data.get('format')}, media_type={data.get('media_type')}")
            print(f"   Base64 data length: {len(data.get('image_data', ''))} characters")
        except:
            print(f"❌ Failed to parse base64 response as JSON")
    else:
        print(f"❌ Failed to get base64 image data: {response.text}")
    
    print("---")
    
    # Test binary thumbnail endpoint
    response = requests.get(f"{BASE_URL}/images/{image_id}/thumbnail", headers=headers)
    print(f"Binary thumbnail response: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
    print(f"Content-Length: {response.headers.get('content-length', 'Not set')}")
    
    if response.status_code == 200:
        content = response.content
        print(f"First 10 bytes: {content[:10]}")
        
        if content.startswith(b'\x89PNG'):
            print("✅ Binary thumbnail is PNG format")
        elif content.startswith(b'\xff\xd8\xff'):
            print("✅ Binary thumbnail is JPEG format")
        else:
            print("⚠️  Unknown binary thumbnail format")
    else:
        print(f"❌ Failed to get binary thumbnail: {response.text}")
    
    print("---")
    
    # Test base64 thumbnail endpoint
    response = requests.get(f"{BASE_URL}/images/{image_id}/thumbnail-base64", headers=headers)
    print(f"Base64 thumbnail response: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✅ Base64 thumbnail data: format={data.get('format')}, media_type={data.get('media_type')}")
            print(f"   Base64 data length: {len(data.get('thumbnail_data', ''))} characters")
        except:
            print(f"❌ Failed to parse base64 thumbnail response as JSON")
    else:
        print(f"❌ Failed to get base64 thumbnail: {response.text}")

def main():
    print("Testing image endpoints...")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token")
        return
    
    print("✅ Got auth token")
    
    # Test the endpoints
    test_image_endpoint(token, IMAGE_ID)

if __name__ == "__main__":
    main()
