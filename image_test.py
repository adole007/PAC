#!/usr/bin/env python3
import requests
import json
import logging
import time
import io
import numpy as np
from PIL import Image
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use local URL for testing
BACKEND_URL = "http://localhost:8001/api"
logger.info(f"Using backend URL: {BACKEND_URL}")

# Test data
ADMIN_CREDENTIALS = {"username": "admin", "password": "password"}
CLINICIAN_CREDENTIALS = {"username": "clinician", "password": "password"}

def login():
    """Login and get tokens"""
    # Login as admin
    response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        logger.error(f"Admin login failed: {response.text}")
        return None
    
    admin_token = response.json()["access_token"]
    logger.info("Admin login successful")
    
    # Login as clinician
    response = requests.post(f"{BACKEND_URL}/auth/login", json=CLINICIAN_CREDENTIALS)
    if response.status_code != 200:
        logger.error(f"Clinician login failed: {response.text}")
        return None
    
    clinician_token = response.json()["access_token"]
    logger.info("Clinician login successful")
    
    return {
        "admin_token": admin_token,
        "clinician_token": clinician_token
    }

def create_test_patient(token):
    """Create a test patient"""
    patient_id = f"PAT{int(time.time())}"
    patient_data = {
        "patient_id": patient_id,
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1985-05-15",
        "gender": "Female",
        "phone": "555-987-6543",
        "email": "jane.smith@example.com",
        "address": "456 Oak St, Anytown, USA",
        "medical_record_number": f"MRN{int(time.time())}",
        "primary_physician": "Dr. John Doe",
        "allergies": ["Sulfa", "Latex"],
        "medications": ["Atorvastatin", "Levothyroxine"],
        "medical_history": ["Hypothyroidism", "Hyperlipidemia"],
        "insurance_provider": "Aetna",
        "insurance_policy_number": f"POL{int(time.time())}",
        "insurance_group_number": f"GRP{int(time.time())}",
        "consent_given": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BACKEND_URL}/patients", json=patient_data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to create patient: {response.text}")
        return None
    
    created_patient = response.json()
    logger.info(f"Created test patient with ID: {created_patient['id']}")
    
    return created_patient

def create_test_image():
    """Create a test image"""
    # Create a simple test image with a gradient
    width, height = 200, 200
    image = Image.new('RGB', (width, height))
    pixels = image.load()
    
    for i in range(width):
        for j in range(height):
            r = int(255 * i / width)
            g = int(255 * j / height)
            b = int(255 * (i + j) / (width + height))
            pixels[i, j] = (r, g, b)
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()

def test_image_upload(token, patient_id):
    """Test image upload functionality"""
    logger.info("Testing image upload...")
    
    headers = {"Authorization": f"Bearer {token}"}
    headers.pop("Content-Type", None)  # Let requests set the correct content type for multipart
    
    # Create test image
    image_data = create_test_image()
    
    # Prepare form data
    files = {
        "file": ("test_image.png", image_data, "image/png")
    }
    
    data = {
        "study_id": f"STUDY{int(time.time())}",
        "series_id": f"SERIES{int(time.time())}",
        "modality": "XR",
        "body_part": "CHEST",
        "study_date": "2023-05-15",
        "study_time": "14:30:00",
        "institution_name": "Test Hospital",
        "referring_physician": "Dr. Smith"
    }
    
    # Upload image
    response = requests.post(
        f"{BACKEND_URL}/patients/{patient_id}/images",
        files=files,
        data=data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to upload image: {response.text}")
        return None
    
    result = response.json()
    logger.info(f"Uploaded image with ID: {result['image_id']}")
    
    return result["image_id"]

def test_get_patient_images(token, patient_id):
    """Test getting patient images"""
    logger.info("Testing get patient images...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/patients/{patient_id}/images",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get patient images: {response.text}")
        return False
    
    images = response.json()
    logger.info(f"Retrieved {len(images)} images for patient")
    
    # Verify image structure
    if images:
        image = images[0]
        required_fields = ["id", "patient_id", "image_data", "thumbnail_data"]
        for field in required_fields:
            if field not in image:
                logger.error(f"Image missing required field: {field}")
                return False
        
        # Verify image data is base64
        if not (image["image_data"].startswith("iVBOR") or 
                image["image_data"].startswith("data:") or
                image["image_data"].startswith("/9j/")):
            logger.error("Image data is not valid base64")
            return False
    
    return True

def test_get_specific_image(token, image_id):
    """Test getting a specific image"""
    logger.info("Testing get specific image...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BACKEND_URL}/images/{image_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get specific image: {response.text}")
        return False
    
    image = response.json()
    logger.info(f"Retrieved image with ID: {image['id']}")
    
    # Verify image structure
    required_fields = ["id", "patient_id", "image_data", "thumbnail_data"]
    for field in required_fields:
        if field not in image:
            logger.error(f"Image missing required field: {field}")
            return False
    
    return True

def test_delete_image(token, image_id):
    """Test deleting an image"""
    logger.info("Testing delete image...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BACKEND_URL}/images/{image_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to delete image: {response.text}")
        return False
    
    result = response.json()
    if result["message"] != "Image deleted successfully":
        logger.error(f"Unexpected delete response: {result}")
        return False
    
    # Verify the image is deleted
    response = requests.get(
        f"{BACKEND_URL}/images/{image_id}",
        headers=headers
    )
    
    if response.status_code != 404:
        logger.error(f"Image not deleted properly: {response.text}")
        return False
    
    logger.info("Image deleted successfully")
    return True

def cleanup(token, patient_id):
    """Clean up test data"""
    logger.info("Cleaning up test data...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Delete the test patient
    response = requests.delete(
        f"{BACKEND_URL}/patients/{patient_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to delete patient: {response.text}")
        return False
    
    # Verify the patient is deleted
    response = requests.get(
        f"{BACKEND_URL}/patients/{patient_id}",
        headers=headers
    )
    
    if response.status_code != 404:
        logger.error(f"Patient not deleted properly: {response.text}")
        return False
    
    logger.info("Test data cleanup completed")
    return True

def run_image_tests():
    """Run image-related tests"""
    logger.info("Starting image-related tests...")
    
    # Login
    tokens = login()
    if not tokens:
        logger.error("Login failed")
        return False
    
    # Create test patient
    patient = create_test_patient(tokens["clinician_token"])
    if not patient:
        logger.error("Failed to create test patient")
        return False
    
    patient_id = patient["id"]
    
    # Test image upload
    image_id = test_image_upload(tokens["clinician_token"], patient_id)
    if not image_id:
        logger.error("Image upload test failed")
        cleanup(tokens["admin_token"], patient_id)
        return False
    
    # Test getting patient images
    if not test_get_patient_images(tokens["clinician_token"], patient_id):
        logger.error("Get patient images test failed")
        cleanup(tokens["admin_token"], patient_id)
        return False
    
    # Test getting specific image
    if not test_get_specific_image(tokens["clinician_token"], image_id):
        logger.error("Get specific image test failed")
        cleanup(tokens["admin_token"], patient_id)
        return False
    
    # Test deleting image
    if not test_delete_image(tokens["clinician_token"], image_id):
        logger.error("Delete image test failed")
        cleanup(tokens["admin_token"], patient_id)
        return False
    
    # Clean up
    if not cleanup(tokens["admin_token"], patient_id):
        logger.error("Cleanup failed")
        return False
    
    logger.info("All image-related tests passed successfully!")
    return True

if __name__ == "__main__":
    run_image_tests()