#!/usr/bin/env python3
"""
Test script for the new image serving endpoints
"""
import requests
import json
import os
import base64
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api"

def test_image_endpoints():
    """Test the new image serving endpoints"""
    print("Testing PAC System Image Endpoints...")
    
    # Step 1: Login to get token
    print("\n1. Logging in...")
    login_data = {
        "username": "clinician",
        "password": "password123"
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print("✗ Login failed")
        return False
    
    # Step 2: Get all patients
    print("\n2. Getting patients...")
    response = requests.get(f"{API_URL}/patients", headers=headers)
    if response.status_code == 200:
        patients = response.json()
        print(f"✓ Found {len(patients)} patients")
        if not patients:
            print("No patients found. Please add some patients first.")
            return False
    else:
        print("✗ Failed to get patients")
        return False
    
    # Step 3: Get images for first patient
    print("\n3. Getting patient images...")
    patient_id = patients[0]["id"]
    response = requests.get(f"{API_URL}/patients/{patient_id}/images", headers=headers)
    if response.status_code == 200:
        images = response.json()
        print(f"✓ Found {len(images)} images for patient")
        if not images:
            print("No images found for patient. Please upload some images first.")
            return False
    else:
        print("✗ Failed to get patient images")
        return False
    
    # Step 4: Test new image data endpoint
    print("\n4. Testing image data endpoint...")
    image_id = images[0]["id"]
    response = requests.get(f"{API_URL}/images/{image_id}/data", headers=headers)
    if response.status_code == 200:
        print(f"✓ Image data endpoint works! Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Image size: {len(response.content)} bytes")
        
        # Save image to file for verification
        image_format = images[0].get("image_format", "png").lower()
        filename = f"test_image.{image_format}"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"  Image saved as: {filename}")
    else:
        print(f"✗ Image data endpoint failed: {response.status_code}")
        return False
    
    # Step 5: Test thumbnail endpoint
    print("\n5. Testing thumbnail endpoint...")
    response = requests.get(f"{API_URL}/images/{image_id}/thumbnail", headers=headers)
    if response.status_code == 200:
        print(f"✓ Thumbnail endpoint works! Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Thumbnail size: {len(response.content)} bytes")
        
        # Save thumbnail to file for verification
        with open("test_thumbnail.png", 'wb') as f:
            f.write(response.content)
        print("  Thumbnail saved as: test_thumbnail.png")
    else:
        print(f"✗ Thumbnail endpoint failed: {response.status_code}")
        return False
    
    # Step 6: Test authentication (should fail without token)
    print("\n6. Testing authentication...")
    response = requests.get(f"{API_URL}/images/{image_id}/data")
    if response.status_code == 401 or response.status_code == 422:
        print("✓ Authentication is working (request without token failed as expected)")
    else:
        print(f"✗ Authentication issue: Expected 401/422, got {response.status_code}")
        return False
    
    print("\n🎉 All tests passed! The new image endpoints are working correctly.")
    return True

def compare_endpoints():
    """Compare the old vs new endpoint performance"""
    print("\nComparing old vs new endpoint performance...")
    
    # Login
    login_data = {"username": "clinician", "password": "password123"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get first image
    patients = requests.get(f"{API_URL}/patients", headers=headers).json()
    patient_id = patients[0]["id"]
    images = requests.get(f"{API_URL}/patients/{patient_id}/images", headers=headers).json()
    image_id = images[0]["id"]
    
    print(f"\nTesting with image: {images[0]['modality']} - {images[0]['body_part']}")
    
    # Test old endpoint (returns full JSON with base64)
    import time
    start_time = time.time()
    response = requests.get(f"{API_URL}/images/{image_id}", headers=headers)
    old_time = time.time() - start_time
    old_size = len(response.content)
    
    # Test new endpoint (returns binary data)
    start_time = time.time()
    response = requests.get(f"{API_URL}/images/{image_id}/data", headers=headers)
    new_time = time.time() - start_time
    new_size = len(response.content)
    
    print(f"\nOld endpoint (/images/{image_id}):")
    print(f"  Time: {old_time:.3f}s")
    print(f"  Size: {old_size:,} bytes")
    
    print(f"\nNew endpoint (/images/{image_id}/data):")
    print(f"  Time: {new_time:.3f}s")
    print(f"  Size: {new_size:,} bytes")
    
    if new_time < old_time:
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"  🚀 {improvement:.1f}% faster!")
    
    if new_size < old_size:
        reduction = ((old_size - new_size) / old_size) * 100
        print(f"  💾 {reduction:.1f}% smaller!")

if __name__ == "__main__":
    print("PAC System Image Endpoints Test")
    print("=" * 40)
    
    if test_image_endpoints():
        compare_endpoints()
    else:
        print("\n❌ Tests failed. Please check your server and database.")
