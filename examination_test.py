#!/usr/bin/env python3
import requests
import json
import logging
from pathlib import Path
import unittest
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use local backend URL for testing since external URL has routing issues
BACKEND_URL = "http://localhost:8001/api"

logger.info(f"Using backend URL: {BACKEND_URL}")

# Test credentials as requested by user
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class ExaminationManagementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_token = None
        cls.test_patient_id = None
        cls.test_examination_id = None
        cls.ct_scanner_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        
        # Login and get token
        cls.login_admin()

    @classmethod
    def login_admin(cls):
        """Login as admin user"""
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                cls.admin_token = response.json()["access_token"]
                logger.info("✅ Admin login successful")
            else:
                logger.error(f"❌ Admin login failed: {response.text}")
                raise Exception(f"Admin login failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error during admin login: {str(e)}")
            raise

    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}

    def test_01_authentication(self):
        """Test 1: Authentication Test - Login with admin credentials"""
        logger.info("🔐 Testing authentication with admin credentials...")
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], "admin")
        
        logger.info("✅ Authentication test passed")

    def test_02_device_management_api(self):
        """Test 2: Device Management API Tests"""
        logger.info("🏥 Testing Device Management API...")
        
        headers = self.get_auth_headers()
        
        # GET /api/devices - Should return the 4 sample devices
        response = requests.get(f"{BACKEND_URL}/devices", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get devices: {response.text}")
        
        devices = response.json()
        logger.info(f"Found {len(devices)} devices")
        
        # Verify we have the expected devices
        device_names = [device['name'] for device in devices]
        expected_devices = ['CT Scanner', 'MRI Scanner', 'X-Ray Machine', 'Ultrasound']
        
        for expected_device in expected_devices:
            found = any(expected_device in name for name in device_names)
            self.assertTrue(found, f"Expected device '{expected_device}' not found in devices")
        
        # Verify each device has proper fields
        for device in devices:
            required_fields = ['id', 'name', 'model', 'manufacturer', 'device_type', 'location', 'specifications']
            for field in required_fields:
                self.assertIn(field, device, f"Device missing required field: {field}")
        
        # Find CT Scanner for later use
        ct_scanner = next((d for d in devices if 'CT' in d['name'] or 'CT' in d['device_type']), None)
        if ct_scanner:
            self.__class__.ct_scanner_id = ct_scanner['id']
            logger.info(f"Found CT Scanner with ID: {ct_scanner['id']}")
        
        logger.info("✅ Device Management API test passed")

    def test_03_patient_examination_api(self):
        """Test 3: Patient Examination API Tests"""
        logger.info("👥 Testing Patient Examination API...")
        
        headers = self.get_auth_headers()
        
        # First get a list of patients from GET /api/patients
        response = requests.get(f"{BACKEND_URL}/patients", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get patients: {response.text}")
        
        patients = response.json()
        self.assertGreater(len(patients), 0, "No patients found in the system")
        
        # Use the first patient for testing
        first_patient = patients[0]
        self.__class__.test_patient_id = first_patient['id']
        logger.info(f"Using patient: {first_patient['first_name']} {first_patient['last_name']} (ID: {first_patient['id']})")
        
        # Test GET /api/patients/{patient_id}/examinations
        response = requests.get(f"{BACKEND_URL}/patients/{first_patient['id']}/examinations", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get patient examinations: {response.text}")
        
        examinations = response.json()
        logger.info(f"Patient has {len(examinations)} existing examinations")
        
        logger.info("✅ Patient Examination API test passed")

    def test_04_create_sample_examination(self):
        """Test 4: Create Sample Examination Test"""
        logger.info("📋 Testing Create Sample Examination...")
        
        headers = self.get_auth_headers()
        
        # Sample examination data as requested
        examination_data = {
            "patient_id": self.test_patient_id,
            "examination_type": "CT Scan",
            "examination_date": "2025-07-10",
            "examination_time": "10:30:00",
            "device_id": self.ct_scanner_id,
            "referring_physician": "Dr. Johnson",
            "performing_physician": "Dr. Smith",
            "body_part_examined": "Chest",
            "clinical_indication": "Chest pain investigation",
            "examination_protocol": "Standard chest CT protocol",
            "priority": "normal"
        }
        
        # Create a new examination
        response = requests.post(f"{BACKEND_URL}/examinations", json=examination_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to create examination: {response.text}")
        
        created_examination = response.json()
        self.assertIn("id", created_examination)
        self.__class__.test_examination_id = created_examination["id"]
        
        logger.info(f"✅ Created examination with ID: {created_examination['id']}")

    def test_05_verification_tests(self):
        """Test 5: Verification Tests"""
        logger.info("✅ Testing Verification of Created Examination...")
        
        headers = self.get_auth_headers()
        
        # Verify the examination was created by calling GET /api/patients/{patient_id}/examinations again
        response = requests.get(f"{BACKEND_URL}/patients/{self.test_patient_id}/examinations", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get patient examinations: {response.text}")
        
        examinations = response.json()
        examination_found = any(exam['id'] == self.test_examination_id for exam in examinations)
        self.assertTrue(examination_found, "Created examination not found in patient's examinations")
        
        # Test GET /api/examinations/{examination_id} to get examination details
        response = requests.get(f"{BACKEND_URL}/examinations/{self.test_examination_id}", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get examination details: {response.text}")
        
        examination_details = response.json()
        self.assertEqual(examination_details['examination_type'], "CT Scan")
        self.assertEqual(examination_details['body_part_examined'], "Chest")
        
        # Test GET /api/examinations/{examination_id}/images (should be empty since no images uploaded yet)
        response = requests.get(f"{BACKEND_URL}/examinations/{self.test_examination_id}/images", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get examination images: {response.text}")
        
        images = response.json()
        self.assertEqual(len(images), 0, "Expected no images for new examination")
        
        # Test GET /api/examinations/{examination_id}/reports (should be empty since no reports created yet)
        response = requests.get(f"{BACKEND_URL}/examinations/{self.test_examination_id}/reports", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to get examination reports: {response.text}")
        
        reports = response.json()
        self.assertEqual(len(reports), 0, "Expected no reports for new examination")
        
        logger.info("✅ Verification tests passed")

    def test_06_error_handling_tests(self):
        """Test 6: Error Handling Tests"""
        logger.info("⚠️ Testing Error Handling...")
        
        headers = self.get_auth_headers()
        
        # Test GET /api/patients/invalid-id/examinations (should return 404 or appropriate error)
        response = requests.get(f"{BACKEND_URL}/patients/invalid-id/examinations", headers=headers)
        self.assertIn(response.status_code, [404, 400], f"Expected 404 or 400 for invalid patient ID, got {response.status_code}")
        
        # Test GET /api/examinations/invalid-id (should return 404)
        response = requests.get(f"{BACKEND_URL}/examinations/invalid-id", headers=headers)
        self.assertIn(response.status_code, [404, 400], f"Expected 404 or 400 for invalid examination ID, got {response.status_code}")
        
        logger.info("✅ Error handling tests passed")

def run_examination_tests():
    """Run all examination management tests"""
    logger.info("🚀 Starting Examination Management System Tests...")
    logger.info(f"Backend URL: {BACKEND_URL}")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ExaminationManagementTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("❌ FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.error("❌ ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_examination_tests()
    exit(0 if success else 1)