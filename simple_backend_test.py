#!/usr/bin/env python3
import requests
import json
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend .env file
def get_backend_url():
    # Use local URL for testing
    return "http://localhost:8001/api"

BACKEND_URL = get_backend_url()

logger.info(f"Using backend URL: {BACKEND_URL}")

# Test data
ADMIN_CREDENTIALS = {"username": "admin", "password": "password"}
CLINICIAN_CREDENTIALS = {"username": "clinician", "password": "password"}

def test_authentication():
    """Test authentication system"""
    logger.info("Testing authentication system...")
    
    # Test user registration (admin)
    admin_data = {
        "username": ADMIN_CREDENTIALS["username"],
        "password": ADMIN_CREDENTIALS["password"],
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_data)
    if response.status_code == 200:
        logger.info("Admin user registered successfully")
    elif response.status_code == 400 and "already registered" in response.text:
        logger.info("Admin user already exists")
    else:
        logger.error(f"Failed to register admin user: {response.text}")
        return False
    
    # Test user registration (clinician)
    clinician_data = {
        "username": CLINICIAN_CREDENTIALS["username"],
        "password": CLINICIAN_CREDENTIALS["password"],
        "email": "clinician@example.com",
        "full_name": "Clinician User",
        "role": "clinician"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/register", json=clinician_data)
    if response.status_code == 200:
        logger.info("Clinician user registered successfully")
    elif response.status_code == 400 and "already registered" in response.text:
        logger.info("Clinician user already exists")
    else:
        logger.error(f"Failed to register clinician user: {response.text}")
        return False
    
    # Test login with valid credentials (admin)
    response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        logger.error(f"Admin login failed: {response.text}")
        return False
    
    admin_token = response.json()["access_token"]
    logger.info("Admin login successful")
    
    # Test login with valid credentials (clinician)
    response = requests.post(f"{BACKEND_URL}/auth/login", json=CLINICIAN_CREDENTIALS)
    if response.status_code != 200:
        logger.error(f"Clinician login failed: {response.text}")
        return False
    
    clinician_token = response.json()["access_token"]
    logger.info("Clinician login successful")
    
    # Test login with invalid credentials
    invalid_credentials = {"username": "admin", "password": "wrongpassword"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=invalid_credentials)
    if response.status_code != 401:
        logger.error(f"Invalid login test failed: {response.text}")
        return False
    
    logger.info("Invalid login test passed")
    
    # Test protected route with valid token
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
    if response.status_code != 200:
        logger.error(f"Protected route test failed: {response.text}")
        return False
    
    if response.json()["username"] != ADMIN_CREDENTIALS["username"]:
        logger.error("Username mismatch in protected route response")
        return False
    
    logger.info("Protected route test passed")
    
    # Test protected route with invalid token
    headers = {"Authorization": "Bearer invalidtoken"}
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
    if response.status_code != 401:
        logger.error(f"Invalid token test failed: {response.text}")
        return False
    
    logger.info("Invalid token test passed")
    logger.info("Authentication system tests passed")
    
    return {
        "admin_token": admin_token,
        "clinician_token": clinician_token
    }

def test_patient_management(tokens):
    """Test patient management CRUD operations"""
    logger.info("Testing patient management...")
    
    if not tokens:
        logger.error("No authentication tokens available")
        return False
    
    admin_token = tokens["admin_token"]
    clinician_token = tokens["clinician_token"]
    
    # Create a test patient
    patient_id = f"PAT{int(time.time())}"
    patient_data = {
        "patient_id": patient_id,
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "gender": "Male",
        "phone": "555-123-4567",
        "email": "john.doe@example.com",
        "address": "123 Main St, Anytown, USA",
        "medical_record_number": f"MRN{int(time.time())}",
        "primary_physician": "Dr. Jane Smith",
        "allergies": ["Penicillin", "Peanuts"],
        "medications": ["Lisinopril", "Metformin"],
        "medical_history": ["Hypertension", "Type 2 Diabetes"],
        "insurance_provider": "Blue Cross Blue Shield",
        "insurance_policy_number": f"POL{int(time.time())}",
        "insurance_group_number": f"GRP{int(time.time())}",
        "consent_given": True
    }
    
    headers = {"Authorization": f"Bearer {clinician_token}"}
    
    # Test creating a patient
    response = requests.post(f"{BACKEND_URL}/patients", json=patient_data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to create patient: {response.text}")
        return False
    
    created_patient = response.json()
    if created_patient["patient_id"] != patient_id:
        logger.error("Patient ID mismatch in created patient")
        return False
    
    test_patient_id = created_patient["id"]
    logger.info(f"Created test patient with ID: {test_patient_id}")
    
    # Test getting all patients
    response = requests.get(f"{BACKEND_URL}/patients", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to get patients: {response.text}")
        return False
    
    patients = response.json()
    if not any(p["id"] == test_patient_id for p in patients):
        logger.error("Created patient not found in patients list")
        return False
    
    logger.info("Get all patients test passed")
    
    # Test getting a specific patient
    response = requests.get(f"{BACKEND_URL}/patients/{test_patient_id}", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to get specific patient: {response.text}")
        return False
    
    patient = response.json()
    if patient["id"] != test_patient_id:
        logger.error("Patient ID mismatch in retrieved patient")
        return False
    
    logger.info("Get specific patient test passed")
    
    # Test updating a patient
    update_data = patient_data.copy()
    update_data["first_name"] = "Jonathan"
    update_data["medical_history"] = ["Hypertension", "Type 2 Diabetes", "Asthma"]
    
    response = requests.put(f"{BACKEND_URL}/patients/{test_patient_id}", 
                           json=update_data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to update patient: {response.text}")
        return False
    
    updated_patient = response.json()
    if updated_patient["first_name"] != "Jonathan" or "Asthma" not in updated_patient["medical_history"]:
        logger.error("Patient update did not apply correctly")
        return False
    
    logger.info("Update patient test passed")
    
    # Test deleting a patient
    response = requests.delete(f"{BACKEND_URL}/patients/{test_patient_id}", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to delete patient: {response.text}")
        return False
    
    # Verify the patient is deleted
    response = requests.get(f"{BACKEND_URL}/patients/{test_patient_id}", headers=headers)
    if response.status_code != 404:
        logger.error(f"Patient not deleted properly: {response.text}")
        return False
    
    logger.info("Delete patient test passed")
    logger.info("Patient management tests passed")
    
    return True

def test_audit_logging(tokens):
    """Test audit logging functionality"""
    logger.info("Testing audit logging...")
    
    if not tokens:
        logger.error("No authentication tokens available")
        return False
    
    admin_token = tokens["admin_token"]
    clinician_token = tokens["clinician_token"]
    
    # Only admin can access audit logs
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test getting audit logs
    response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to get audit logs: {response.text}")
        return False
    
    logs = response.json()
    if not isinstance(logs, list):
        logger.error("Audit logs response is not a list")
        return False
    
    logger.info(f"Retrieved {len(logs)} audit logs")
    
    # Verify audit log structure
    if logs:
        log = logs[0]
        required_fields = ["id", "user_id", "action", "resource_type", "resource_id", "timestamp"]
        for field in required_fields:
            if field not in log:
                logger.error(f"Audit log missing required field: {field}")
                return False
    
    # Test that clinician cannot access audit logs
    headers = {"Authorization": f"Bearer {clinician_token}"}
    response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers)
    if response.status_code != 403:
        logger.error(f"Clinician should not be able to access audit logs: {response.text}")
        return False
    
    logger.info("Audit logging tests passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting PAC System backend tests...")
    
    # Test authentication
    tokens = test_authentication()
    if not tokens:
        logger.error("Authentication tests failed")
        return False
    
    # Test patient management
    if not test_patient_management(tokens):
        logger.error("Patient management tests failed")
        return False
    
    # Test audit logging
    if not test_audit_logging(tokens):
        logger.error("Audit logging tests failed")
        return False
    
    logger.info("All tests passed successfully!")
    return True

if __name__ == "__main__":
    run_tests()