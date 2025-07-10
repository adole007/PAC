#!/usr/bin/env python3
import requests
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend .env file
def get_backend_url():
    env_path = Path('/app/frontend/.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.strip().split('=')[1].strip('"\'') + '/api'
    return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    raise ValueError("Backend URL not found in frontend/.env")

logger.info(f"Using backend URL: {BACKEND_URL}")

# Test credentials
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def login_admin():
    """Login as admin user"""
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            token = response.json()["access_token"]
            logger.info("✅ Admin login successful")
            return token
        else:
            logger.error(f"❌ Admin login failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error during admin login: {str(e)}")
        return None

def create_sample_devices(token):
    """Create the 4 sample devices"""
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_devices = [
        {
            "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "name": "CT Scanner",
            "model": "Siemens SOMATOM Definition AS",
            "manufacturer": "Siemens Healthineers",
            "device_type": "CT",
            "location": "Radiology Department - Room 101",
            "specifications": {
                "slice_thickness": "0.6mm",
                "rotation_time": "0.28s",
                "detector_rows": "128",
                "max_power": "100kW"
            }
        },
        {
            "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "name": "MRI Scanner",
            "model": "Philips Ingenia 3.0T",
            "manufacturer": "Philips Healthcare",
            "device_type": "MRI",
            "location": "Radiology Department - Room 102",
            "specifications": {
                "field_strength": "3.0 Tesla",
                "bore_diameter": "70cm",
                "gradient_strength": "45mT/m",
                "slew_rate": "200T/m/s"
            }
        },
        {
            "id": "b2c3d4e5-f6g7-8901-2345-678901bcdefg",
            "name": "X-Ray Machine",
            "model": "GE Discovery XR656",
            "manufacturer": "GE Healthcare",
            "device_type": "X-Ray",
            "location": "Emergency Department - Room 201",
            "specifications": {
                "tube_voltage": "150kV",
                "tube_current": "800mA",
                "detector_size": "43cm x 43cm",
                "pixel_size": "139μm"
            }
        },
        {
            "id": "c3d4e5f6-g7h8-9012-3456-789012cdefgh",
            "name": "Ultrasound",
            "model": "Mindray DC-70",
            "manufacturer": "Mindray Medical",
            "device_type": "Ultrasound",
            "location": "Cardiology Department - Room 301",
            "specifications": {
                "frequency_range": "2-15 MHz",
                "display_size": "21.5 inch",
                "probe_types": "Linear, Convex, Phased Array",
                "doppler_modes": "Color, Power, PW, CW"
            }
        }
    ]
    
    created_devices = []
    for device_data in sample_devices:
        try:
            response = requests.post(f"{BACKEND_URL}/devices", json=device_data, headers=headers)
            if response.status_code == 200:
                created_device = response.json()
                created_devices.append(created_device)
                logger.info(f"✅ Created device: {device_data['name']}")
            else:
                logger.error(f"❌ Failed to create device {device_data['name']}: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating device {device_data['name']}: {str(e)}")
    
    return created_devices

def main():
    """Setup sample data for examination management system"""
    logger.info("🚀 Setting up sample data for examination management system...")
    
    # Login
    token = login_admin()
    if not token:
        logger.error("❌ Failed to login, cannot setup sample data")
        return False
    
    # Create sample devices
    devices = create_sample_devices(token)
    logger.info(f"✅ Created {len(devices)} sample devices")
    
    # Verify devices were created
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/devices", headers=headers)
    if response.status_code == 200:
        all_devices = response.json()
        logger.info(f"✅ Total devices in system: {len(all_devices)}")
        for device in all_devices:
            logger.info(f"  - {device['name']} ({device['device_type']}) - ID: {device['id']}")
    else:
        logger.error(f"❌ Failed to verify devices: {response.text}")
    
    logger.info("🎉 Sample data setup complete!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)