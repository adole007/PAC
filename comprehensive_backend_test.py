#!/usr/bin/env python3
import requests
import json
import base64
import os
import unittest
import logging
from pathlib import Path
import io
import random
import string
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend .env file
def get_backend_url():
    # Use local URL for testing
    return "http://localhost:8001/api"

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    raise ValueError("Backend URL not found in frontend/.env")

logger.info(f"Using backend URL: {BACKEND_URL}")

# Test data
ADMIN_CREDENTIALS = {"username": "admin", "password": "password"}
CLINICIAN_CREDENTIALS = {"username": "clinician", "password": "password"}

# Helper function to generate random string
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class PACSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_token = None
        cls.clinician_token = None
        cls.test_patient_id = None
        cls.test_image_id = None
        cls.dicom_image_id = None
        cls.standard_image_id = None
        
        # Create test users if they don't exist
        cls.register_test_users()
        
        # Login and get tokens
        cls.login_users()
        
        # Create a test patient for image tests
        cls.create_test_patient()

    @classmethod
    def register_test_users(cls):
        # Try to register admin user
        admin_data = {
            "username": ADMIN_CREDENTIALS["username"],
            "password": ADMIN_CREDENTIALS["password"],
            "email": "admin@example.com",
            "full_name": "Admin User",
            "role": "admin"
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_data)
            if response.status_code == 200:
                logger.info("Admin user registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                logger.info("Admin user already exists")
            else:
                logger.warning(f"Failed to register admin user: {response.text}")
        except Exception as e:
            logger.error(f"Error registering admin user: {str(e)}")
        
        # Try to register clinician user
        clinician_data = {
            "username": CLINICIAN_CREDENTIALS["username"],
            "password": CLINICIAN_CREDENTIALS["password"],
            "email": "clinician@example.com",
            "full_name": "Clinician User",
            "role": "clinician"
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/register", json=clinician_data)
            if response.status_code == 200:
                logger.info("Clinician user registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                logger.info("Clinician user already exists")
            else:
                logger.warning(f"Failed to register clinician user: {response.text}")
        except Exception as e:
            logger.error(f"Error registering clinician user: {str(e)}")

    @classmethod
    def login_users(cls):
        # Login as admin
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                cls.admin_token = response.json()["access_token"]
                logger.info("Admin login successful")
            else:
                logger.error(f"Admin login failed: {response.text}")
        except Exception as e:
            logger.error(f"Error during admin login: {str(e)}")
        
        # Login as clinician
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=CLINICIAN_CREDENTIALS)
            if response.status_code == 200:
                cls.clinician_token = response.json()["access_token"]
                logger.info("Clinician login successful")
            else:
                logger.error(f"Clinician login failed: {response.text}")
        except Exception as e:
            logger.error(f"Error during clinician login: {str(e)}")

    @classmethod
    def create_test_patient(cls):
        if not cls.clinician_token:
            logger.error("No clinician token available, cannot create test patient")
            return
            
        # Create a test patient
        patient_id = f"PAT{random_string(8)}"
        patient_data = {
            "patient_id": patient_id,
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-15",
            "gender": "Female",
            "phone": "555-987-6543",
            "email": "jane.smith@example.com",
            "address": "456 Oak St, Somewhere, USA",
            "medical_record_number": f"MRN{random_string(8)}",
            "primary_physician": "Dr. Robert Johnson",
            "allergies": ["Sulfa", "Latex"],
            "medications": ["Atorvastatin", "Levothyroxine"],
            "medical_history": ["Hypothyroidism", "Hyperlipidemia"],
            "insurance_provider": "Aetna",
            "insurance_policy_number": f"POL{random_string(8)}",
            "insurance_group_number": f"GRP{random_string(8)}",
            "consent_given": True
        }
        
        headers = {"Authorization": f"Bearer {cls.clinician_token}"}
        
        try:
            response = requests.post(f"{BACKEND_URL}/patients", json=patient_data, headers=headers)
            if response.status_code == 200:
                created_patient = response.json()
                cls.test_patient_id = created_patient["id"]
                logger.info(f"Created test patient with ID: {cls.test_patient_id}")
            else:
                logger.error(f"Failed to create test patient: {response.text}")
        except Exception as e:
            logger.error(f"Error creating test patient: {str(e)}")

    def test_01_authentication(self):
        """Test authentication system"""
        logger.info("Testing authentication system...")
        
        # Test login with valid credentials
        response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["role"], "admin")
        
        # Test login with invalid credentials
        invalid_credentials = {"username": "admin", "password": "wrongpassword"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=invalid_credentials)
        self.assertEqual(response.status_code, 401)
        
        # Test protected route with valid token
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], ADMIN_CREDENTIALS["username"])
        
        # Test protected route with invalid token
        headers = {"Authorization": "Bearer invalidtoken"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)
        
        logger.info("Authentication system tests passed")

    def test_02_patient_management(self):
        """Test patient management CRUD operations"""
        logger.info("Testing patient management...")
        
        # Create a test patient
        patient_id = f"PAT{random_string(8)}"
        patient_data = {
            "patient_id": patient_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-01",
            "gender": "Male",
            "phone": "555-123-4567",
            "email": "john.doe@example.com",
            "address": "123 Main St, Anytown, USA",
            "medical_record_number": f"MRN{random_string(8)}",
            "primary_physician": "Dr. Jane Smith",
            "allergies": ["Penicillin", "Peanuts"],
            "medications": ["Lisinopril", "Metformin"],
            "medical_history": ["Hypertension", "Type 2 Diabetes"],
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_policy_number": f"POL{random_string(8)}",
            "insurance_group_number": f"GRP{random_string(8)}",
            "consent_given": True
        }
        
        headers = {"Authorization": f"Bearer {self.clinician_token}"}
        
        # Test creating a patient
        response = requests.post(f"{BACKEND_URL}/patients", json=patient_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        created_patient = response.json()
        self.assertEqual(created_patient["patient_id"], patient_id)
        self.assertEqual(created_patient["first_name"], "John")
        self.assertEqual(created_patient["last_name"], "Doe")
        self.assertEqual(created_patient["consent_given"], True)
        
        # Save the patient ID for later tests
        patient_test_id = created_patient["id"]
        logger.info(f"Created test patient with ID: {patient_test_id}")
        
        # Test getting all patients
        response = requests.get(f"{BACKEND_URL}/patients", headers=headers)
        self.assertEqual(response.status_code, 200)
        patients = response.json()
        self.assertIsInstance(patients, list)
        self.assertTrue(any(p["id"] == patient_test_id for p in patients))
        
        # Test getting a specific patient
        response = requests.get(f"{BACKEND_URL}/patients/{patient_test_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        patient = response.json()
        self.assertEqual(patient["id"], patient_test_id)
        
        # Test updating a patient
        update_data = patient_data.copy()
        update_data["first_name"] = "Jonathan"
        update_data["medical_history"] = ["Hypertension", "Type 2 Diabetes", "Asthma"]
        
        response = requests.put(f"{BACKEND_URL}/patients/{patient_test_id}", 
                               json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_patient = response.json()
        self.assertEqual(updated_patient["first_name"], "Jonathan")
        self.assertIn("Asthma", updated_patient["medical_history"])
        
        # Test deleting a patient
        response = requests.delete(f"{BACKEND_URL}/patients/{patient_test_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["message"], "Patient deleted successfully")
        
        # Verify the patient is deleted
        response = requests.get(f"{BACKEND_URL}/patients/{patient_test_id}", headers=headers)
        self.assertEqual(response.status_code, 404)
        
        logger.info("Patient management tests passed")

    def test_03_dicom_image_processing(self):
        """Test DICOM image processing"""
        logger.info("Testing DICOM image processing...")
        
        # Skip if no patient ID is available
        if not self.__class__.test_patient_id:
            self.skipTest("No test patient available")
        
        # Create a simple test DICOM file
        try:
            import pydicom
            from pydicom.dataset import Dataset, FileMetaDataset
            import numpy as np
            from PIL import Image
            
            # Create a simple DICOM dataset
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
            file_meta.MediaStorageSOPInstanceUID = '1.2.3'
            file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'  # Explicit VR Little Endian
            file_meta.ImplementationClassUID = '1.2.3.4'
            
            ds = Dataset()
            ds.file_meta = file_meta
            ds.is_little_endian = True
            ds.is_implicit_VR = False
            ds.PatientName = "Test^Patient"
            ds.PatientID = "TEST12345"
            ds.Modality = "CT"
            ds.StudyInstanceUID = "1.2.3.4"
            ds.SeriesInstanceUID = "1.2.3.4.5"
            ds.SOPInstanceUID = "1.2.3.4.5.6"
            ds.StudyDate = "20230101"
            ds.StudyTime = "120000"
            ds.InstitutionName = "Test Hospital"
            ds.ReferringPhysicianName = "Dr. Referring"
            ds.WindowCenter = 40
            ds.WindowWidth = 80
            
            # Create a simple 32x32 image
            pixel_array = np.zeros((32, 32), dtype=np.uint16)
            for i in range(32):
                for j in range(32):
                    pixel_array[i, j] = i * j
            
            ds.PixelData = pixel_array.tobytes()
            ds.Rows = 32
            ds.Columns = 32
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            
            # Save the DICOM file
            dicom_path = "/tmp/test.dcm"
            ds.save_as(dicom_path)
            logger.info(f"Created test DICOM file at {dicom_path}")
            
            # Upload the DICOM file
            headers = {"Authorization": f"Bearer {self.clinician_token}"}
            
            with open(dicom_path, "rb") as f:
                files = {"file": ("test.dcm", f, "application/dicom")}
                data = {
                    "study_id": "STUDY123",
                    "series_id": "SERIES456",
                    "modality": "CT",
                    "body_part": "HEAD",
                    "study_date": "2023-01-01",
                    "study_time": "12:00:00",
                    "institution_name": "Test Hospital",
                    "referring_physician": "Dr. Referring"
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}/images",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertIn("image_id", result)
                self.assertIn("message", result)
                self.assertEqual(result["message"], "Image uploaded successfully")
                
                # Save the image ID for later tests
                self.__class__.dicom_image_id = result["image_id"]
                logger.info(f"Uploaded DICOM image with ID: {self.__class__.dicom_image_id}")
                
                # Retrieve the image to verify DICOM metadata and windowing parameters
                response = requests.get(
                    f"{BACKEND_URL}/images/{self.__class__.dicom_image_id}",
                    headers=headers
                )
                
                self.assertEqual(response.status_code, 200)
                image_data = response.json()
                
                # Verify DICOM-specific fields
                self.assertEqual(image_data["image_format"], "DICOM")
                self.assertIsNotNone(image_data["window_center"])
                self.assertIsNotNone(image_data["window_width"])
                self.assertIsNotNone(image_data["dicom_metadata"])
                
                # Verify the image data is present
                self.assertIn("image_data", image_data)
                self.assertIn("thumbnail_data", image_data)
                
            
        except ImportError as e:
            logger.error(f"Could not import required modules for DICOM test: {str(e)}")
            self.skipTest(f"Missing required modules: {str(e)}")
        except Exception as e:
            logger.error(f"Error in DICOM test: {str(e)}")
            self.fail(f"DICOM test failed: {str(e)}")
        
        logger.info("DICOM image processing tests passed")

    def test_04_standard_image_processing(self):
        """Test standard image processing (JPEG, PNG)"""
        logger.info("Testing standard image processing...")
        
        # Skip if no patient ID is available
        if not self.__class__.test_patient_id:
            self.skipTest("No test patient available")
        
        try:
            from PIL import Image
            import numpy as np
            
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color=(73, 109, 137))
            img_path = "/tmp/test_image.png"
            img.save(img_path)
            logger.info(f"Created test PNG image at {img_path}")
            
            # Upload the image
            headers = {"Authorization": f"Bearer {self.clinician_token}"}
            
            with open(img_path, "rb") as f:
                files = {"file": ("test_image.png", f, "image/png")}
                data = {
                    "study_id": "STUDY789",
                    "series_id": "SERIES101",
                    "modality": "XR",
                    "body_part": "CHEST",
                    "study_date": "2023-02-01",
                    "study_time": "14:30:00",
                    "institution_name": "Test Hospital",
                    "referring_physician": "Dr. Smith"
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}/images",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertIn("image_id", result)
                self.assertEqual(result["message"], "Image uploaded successfully")
                
                # Save the image ID for later tests
                self.__class__.standard_image_id = result["image_id"]
                logger.info(f"Uploaded standard image with ID: {self.__class__.standard_image_id}")
                
                # Retrieve the image to verify standard image processing
                response = requests.get(
                    f"{BACKEND_URL}/images/{self.__class__.standard_image_id}",
                    headers=headers
                )
                
                self.assertEqual(response.status_code, 200)
                image_data = response.json()
                
                # Verify standard image fields
                self.assertEqual(image_data["image_format"], "PNG")
                self.assertIsNone(image_data["window_center"])
                self.assertIsNone(image_data["window_width"])
                
                # Verify the image data is present
                self.assertIn("image_data", image_data)
                self.assertIn("thumbnail_data", image_data)
            
        except ImportError as e:
            logger.error(f"Could not import required modules for image test: {str(e)}")
            self.skipTest(f"Missing required modules: {str(e)}")
        except Exception as e:
            logger.error(f"Error in standard image test: {str(e)}")
            self.fail(f"Standard image test failed: {str(e)}")
        
        logger.info("Standard image processing tests passed")

    def test_05_image_management(self):
        """Test image management operations"""
        logger.info("Testing image management...")
        
        # Skip if no patient ID is available
        if not self.__class__.test_patient_id:
            self.skipTest("No test patient available")
        
        headers = {"Authorization": f"Bearer {self.clinician_token}"}
        
        # Test getting all images for a patient
        response = requests.get(
            f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}/images",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        images = response.json()
        self.assertIsInstance(images, list)
        self.assertTrue(len(images) >= 1)
        
        # Test getting a specific DICOM image
        if self.__class__.dicom_image_id:
            response = requests.get(
                f"{BACKEND_URL}/images/{self.__class__.dicom_image_id}",
                headers=headers
            )
            self.assertEqual(response.status_code, 200)
            image = response.json()
            self.assertEqual(image["id"], self.__class__.dicom_image_id)
            self.assertEqual(image["patient_id"], self.__class__.test_patient_id)
            
            # Verify image data is present
            self.assertIn("image_data", image)
            self.assertIn("thumbnail_data", image)
            self.assertTrue(image["image_data"].startswith("iVBOR") or image["image_data"].startswith("data:"))
        
        # Test getting a specific standard image
        if self.__class__.standard_image_id:
            response = requests.get(
                f"{BACKEND_URL}/images/{self.__class__.standard_image_id}",
                headers=headers
            )
            self.assertEqual(response.status_code, 200)
            image = response.json()
            self.assertEqual(image["id"], self.__class__.standard_image_id)
            self.assertEqual(image["patient_id"], self.__class__.test_patient_id)
            
            # Verify image data is present
            self.assertIn("image_data", image)
            self.assertIn("thumbnail_data", image)
            self.assertTrue(image["image_data"].startswith("iVBOR") or image["image_data"].startswith("data:"))
        
        # Test deleting an image
        if self.__class__.dicom_image_id:
            response = requests.delete(
                f"{BACKEND_URL}/images/{self.__class__.dicom_image_id}",
                headers=headers
            )
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertEqual(result["message"], "Image deleted successfully")
            
            # Verify the image is deleted
            response = requests.get(
                f"{BACKEND_URL}/images/{self.__class__.dicom_image_id}",
                headers=headers
            )
            self.assertEqual(response.status_code, 404)
        
        logger.info("Image management tests passed")

    def test_06_audit_logging(self):
        """Test audit logging functionality"""
        logger.info("Testing audit logging...")
        
        # Only admin can access audit logs
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test getting audit logs
        response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers)
        self.assertEqual(response.status_code, 200)
        logs = response.json()
        self.assertIsInstance(logs, list)
        
        # Verify audit log structure
        if logs:
            log = logs[0]
            self.assertIn("id", log)
            self.assertIn("user_id", log)
            self.assertIn("action", log)
            self.assertIn("resource_type", log)
            self.assertIn("resource_id", log)
            self.assertIn("timestamp", log)
            self.assertIn("ip_address", log)
            self.assertIn("user_agent", log)
            self.assertIn("details", log)
        
        # Test that clinician cannot access audit logs
        headers = {"Authorization": f"Bearer {self.clinician_token}"}
        response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers)
        self.assertEqual(response.status_code, 403)
        
        logger.info("Audit logging tests passed")

    def test_07_hipaa_compliance(self):
        """Test HIPAA compliance features"""
        logger.info("Testing HIPAA compliance features...")
        
        # Skip if no patient ID is available
        if not self.__class__.test_patient_id:
            self.skipTest("No test patient available")
        
        headers = {"Authorization": f"Bearer {self.clinician_token}"}
        
        # Test patient consent tracking
        response = requests.get(
            f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        patient = response.json()
        self.assertIn("consent_given", patient)
        self.assertIn("last_accessed", patient)
        self.assertIn("access_log", patient)
        
        # Test that access is logged
        # First access was already done above, now check if it was logged
        response = requests.get(
            f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        patient = response.json()
        self.assertIsNotNone(patient["last_accessed"])
        
        # Check audit logs for this patient (admin only)
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BACKEND_URL}/audit-logs", headers=headers)
        self.assertEqual(response.status_code, 200)
        logs = response.json()
        
        # Verify there are logs for this patient
        patient_logs = [log for log in logs if log["resource_id"] == self.__class__.test_patient_id]
        self.assertTrue(len(patient_logs) > 0)
        
        logger.info("HIPAA compliance tests passed")

    def test_08_cleanup(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete the standard image if it exists
        if self.__class__.standard_image_id:
            try:
                response = requests.delete(
                    f"{BACKEND_URL}/images/{self.__class__.standard_image_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    logger.info(f"Deleted standard image with ID: {self.__class__.standard_image_id}")
                else:
                    logger.warning(f"Failed to delete standard image: {response.text}")
            except Exception as e:
                logger.error(f"Error deleting standard image: {str(e)}")
        
        # Delete the test patient
        if self.__class__.test_patient_id:
            try:
                response = requests.delete(
                    f"{BACKEND_URL}/patients/{self.__class__.test_patient_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    logger.info(f"Deleted test patient with ID: {self.__class__.test_patient_id}")
                else:
                    logger.warning(f"Failed to delete test patient: {response.text}")
            except Exception as e:
                logger.error(f"Error deleting test patient: {str(e)}")
        
        logger.info("Test data cleanup completed")

if __name__ == "__main__":
    unittest.main(verbosity=2)