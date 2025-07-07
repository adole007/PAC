from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import uuid
import base64
import json
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import pydicom
import numpy as np
from PIL import Image
import io

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="PAC System API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    role: str  # 'clinician' or 'admin'
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Patient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Basic Demographics
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    phone: str
    email: Optional[EmailStr] = None
    address: str
    
    # Medical Information
    medical_record_number: str
    primary_physician: str
    allergies: List[str] = []
    medications: List[str] = []
    medical_history: List[str] = []
    
    # Insurance Information
    insurance_provider: str
    insurance_policy_number: str
    insurance_group_number: Optional[str] = None
    
    # System Information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    # HIPAA Compliance
    consent_given: bool = False
    last_accessed: Optional[datetime] = None
    access_log: List[Dict[str, Any]] = []

class PatientCreate(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    phone: str
    email: Optional[EmailStr] = None
    address: str
    medical_record_number: str
    primary_physician: str
    allergies: List[str] = []
    medications: List[str] = []
    medical_history: List[str] = []
    insurance_provider: str
    insurance_policy_number: str
    insurance_group_number: Optional[str] = None
    consent_given: bool = False

class MedicalImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    study_id: str
    series_id: str
    instance_id: str
    
    # Image metadata
    modality: str  # CT, MRI, X-Ray, etc.
    body_part: str
    study_date: str
    study_time: str
    institution_name: str
    referring_physician: str
    
    # DICOM specific fields
    dicom_metadata: Dict[str, Any] = {}
    
    # Image data (stored as base64)
    image_data: str
    thumbnail_data: str
    
    # File information
    original_filename: str
    file_size: int
    image_format: str  # 'DICOM', 'JPEG', 'PNG', etc.
    
    # Windowing information for medical images
    window_center: Optional[float] = None
    window_width: Optional[float] = None
    
    # System information
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str
    
    # HIPAA Compliance
    access_log: List[Dict[str, Any]] = []

class ImageUpload(BaseModel):
    patient_id: str
    study_id: str
    series_id: str
    modality: str
    body_part: str
    study_date: str
    study_time: str
    institution_name: str
    referring_physician: str

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: str
    user_agent: str
    details: Dict[str, Any] = {}

# ==================== AUTHENTICATION ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(**user)

# ==================== DICOM PROCESSING ====================

def process_dicom_file(file_content: bytes):
    """Process DICOM file and extract metadata and image data"""
    try:
        # Read DICOM file
        ds = pydicom.dcmread(io.BytesIO(file_content))
        
        # Extract metadata
        metadata = {}
        for elem in ds:
            if elem.tag.group != 0x7fe0:  # Skip pixel data
                try:
                    metadata[str(elem.tag)] = str(elem.value)
                except:
                    pass
        
        # Extract image data
        if hasattr(ds, 'pixel_array'):
            pixel_array = ds.pixel_array
            
            # Apply windowing if available
            window_center = getattr(ds, 'WindowCenter', None)
            window_width = getattr(ds, 'WindowWidth', None)
            
            if window_center and window_width:
                # Convert to appropriate type
                if isinstance(window_center, (list, tuple)):
                    window_center = window_center[0]
                if isinstance(window_width, (list, tuple)):
                    window_width = window_width[0]
                
                # Apply windowing
                img_min = window_center - window_width // 2
                img_max = window_center + window_width // 2
                pixel_array = np.clip(pixel_array, img_min, img_max)
            
            # Normalize to 0-255 range
            pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(pixel_array)
            
            # Create thumbnail
            thumbnail = image.copy()
            thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Convert to base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            thumb_buffer = io.BytesIO()
            thumbnail.save(thumb_buffer, format='PNG')
            thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
            
            return {
                'metadata': metadata,
                'image_data': img_base64,
                'thumbnail_data': thumb_base64,
                'window_center': float(window_center) if window_center else None,
                'window_width': float(window_width) if window_width else None
            }
        
        return {
            'metadata': metadata,
            'image_data': None,
            'thumbnail_data': None,
            'window_center': None,
            'window_width': None
        }
        
    except Exception as e:
        logger.error(f"Error processing DICOM file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing DICOM file: {str(e)}")

def process_standard_image(file_content: bytes):
    """Process standard image file (JPEG, PNG, etc.)"""
    try:
        # Open image
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Convert to base64
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='PNG')
        thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
        
        return {
            'metadata': {},
            'image_data': img_base64,
            'thumbnail_data': thumb_base64,
            'window_center': None,
            'window_width': None
        }
        
    except Exception as e:
        logger.error(f"Error processing image file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing image file: {str(e)}")

# ==================== AUDIT LOGGING ====================

async def log_audit_event(user_id: str, action: str, resource_type: str, resource_id: str, 
                         ip_address: str, user_agent: str, details: Dict[str, Any] = None):
    """Log audit event for HIPAA compliance"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )
    await db.audit_logs.insert_one(audit_log.dict())

# ==================== ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Find user
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db.users.update_one(
        {"username": user_credentials.username},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== PATIENT ROUTES ====================

@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate, current_user: User = Depends(get_current_user)):
    # Check if patient ID already exists
    existing_patient = await db.patients.find_one({"patient_id": patient_data.patient_id})
    if existing_patient:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    # Create patient
    patient = Patient(**patient_data.dict(), created_by=current_user.id)
    await db.patients.insert_one(patient.dict())
    
    # Log audit event
    await log_audit_event(
        current_user.id, "CREATE", "patient", patient.id,
        "127.0.0.1", "API Client", {"patient_id": patient.patient_id}
    )
    
    return patient

@api_router.get("/patients", response_model=List[Patient])
async def get_patients(current_user: User = Depends(get_current_user)):
    patients = await db.patients.find().to_list(1000)
    return [Patient(**patient) for patient in patients]

@api_router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update last accessed
    await db.patients.update_one(
        {"id": patient_id},
        {"$set": {"last_accessed": datetime.utcnow()}}
    )
    
    # Log audit event
    await log_audit_event(
        current_user.id, "READ", "patient", patient_id,
        "127.0.0.1", "API Client"
    )
    
    return Patient(**patient)

@api_router.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(patient_id: str, patient_data: PatientCreate, current_user: User = Depends(get_current_user)):
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update patient
    update_data = patient_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.patients.update_one({"id": patient_id}, {"$set": update_data})
    
    # Log audit event
    await log_audit_event(
        current_user.id, "UPDATE", "patient", patient_id,
        "127.0.0.1", "API Client"
    )
    
    updated_patient = await db.patients.find_one({"id": patient_id})
    return Patient(**updated_patient)

@api_router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Delete patient and associated images
    await db.patients.delete_one({"id": patient_id})
    await db.medical_images.delete_many({"patient_id": patient_id})
    
    # Log audit event
    await log_audit_event(
        current_user.id, "DELETE", "patient", patient_id,
        "127.0.0.1", "API Client"
    )
    
    return {"message": "Patient deleted successfully"}

# ==================== MEDICAL IMAGE ROUTES ====================

@api_router.post("/patients/{patient_id}/images")
async def upload_medical_image(
    patient_id: str,
    file: UploadFile = File(...),
    study_id: str = Form(...),
    series_id: str = Form(...),
    modality: str = Form(...),
    body_part: str = Form(...),
    study_date: str = Form(...),
    study_time: str = Form(...),
    institution_name: str = Form(...),
    referring_physician: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    # Check if patient exists
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Read file content
    file_content = await file.read()
    
    # Determine file type and process accordingly
    is_dicom = file.filename.lower().endswith('.dcm') or file.content_type == 'application/dicom'
    
    if is_dicom:
        processed_data = process_dicom_file(file_content)
        image_format = 'DICOM'
    else:
        processed_data = process_standard_image(file_content)
        image_format = file.content_type.split('/')[-1].upper()
    
    # Create medical image record
    medical_image = MedicalImage(
        patient_id=patient_id,
        study_id=study_id,
        series_id=series_id,
        instance_id=str(uuid.uuid4()),
        modality=modality,
        body_part=body_part,
        study_date=study_date,
        study_time=study_time,
        institution_name=institution_name,
        referring_physician=referring_physician,
        dicom_metadata=processed_data['metadata'],
        image_data=processed_data['image_data'],
        thumbnail_data=processed_data['thumbnail_data'],
        original_filename=file.filename,
        file_size=len(file_content),
        image_format=image_format,
        window_center=processed_data['window_center'],
        window_width=processed_data['window_width'],
        uploaded_by=current_user.id
    )
    
    await db.medical_images.insert_one(medical_image.dict())
    
    # Log audit event
    await log_audit_event(
        current_user.id, "UPLOAD", "medical_image", medical_image.id,
        "127.0.0.1", "API Client", {"patient_id": patient_id, "filename": file.filename}
    )
    
    return {"message": "Image uploaded successfully", "image_id": medical_image.id}

@api_router.get("/patients/{patient_id}/images", response_model=List[MedicalImage])
async def get_patient_images(patient_id: str, current_user: User = Depends(get_current_user)):
    # Check if patient exists
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    images = await db.medical_images.find({"patient_id": patient_id}).to_list(1000)
    
    # Log audit event
    await log_audit_event(
        current_user.id, "READ", "medical_images", patient_id,
        "127.0.0.1", "API Client"
    )
    
    return [MedicalImage(**image) for image in images]

@api_router.get("/images/{image_id}", response_model=MedicalImage)
async def get_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    image = await db.medical_images.find_one({"id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Log audit event
    await log_audit_event(
        current_user.id, "READ", "medical_image", image_id,
        "127.0.0.1", "API Client"
    )
    
    return MedicalImage(**image)

@api_router.delete("/images/{image_id}")
async def delete_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    image = await db.medical_images.find_one({"id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    await db.medical_images.delete_one({"id": image_id})
    
    # Log audit event
    await log_audit_event(
        current_user.id, "DELETE", "medical_image", image_id,
        "127.0.0.1", "API Client"
    )
    
    return {"message": "Image deleted successfully"}

# ==================== AUDIT ROUTES ====================

@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await db.audit_logs.find().sort("timestamp", -1).to_list(1000)
    return [AuditLog(**log) for log in logs]

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)