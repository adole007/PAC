from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
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
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import pydicom
import numpy as np
from PIL import Image
import io

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env.mysql')

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MySQL connection details
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'pac_user'),
    'password': os.environ.get('MYSQL_PASSWORD', 'pac_password'),
    'database': os.environ.get('MYSQL_DATABASE', 'jajuwa_pac_system'),
    'port': int(os.environ.get('MYSQL_PORT', '3306'))
}

# Create the main app
app = FastAPI(title="PAC System API with MySQL", version="1.0.0")
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

# ==================== DATABASE HELPERS ====================

def get_db_connection():
    """Get MySQL database connection"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def dict_from_row(cursor, row):
    """Convert MySQL row to dictionary"""
    if row is None:
        return None
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row))

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
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

# ==================== AUTHENTICATION ====================

def verify_password(plain_password, hashed_password):
    """Verify password with fallback for different hash formats"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        # Fallback: check if it's a simple hash (for development)
        if hashed_password == plain_password:
            return True
        return False

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

# ==================== IMAGE PROCESSING ====================

def process_dicom_file(file_content: bytes):
    """Process DICOM file and extract metadata and image data"""
    try:
        # Read DICOM file with force=True to handle files without proper headers
        ds = pydicom.dcmread(io.BytesIO(file_content), force=True)
        
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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_row = cursor.fetchone()
    
    if user_row is None:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_dict = dict_from_row(cursor, user_row)
    conn.close()
    
    return User(**user_dict)

# ==================== ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = %s", (user_data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    cursor.execute("""
        INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, user_data.username, user_data.email, user_data.full_name, 
          hashed_password, user_data.role, now))
    
    conn.commit()
    conn.close()
    
    return User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        created_at=now
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user
    cursor.execute("SELECT * FROM users WHERE username = %s", (user_credentials.username,))
    user_row = cursor.fetchone()
    
    if not user_row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_dict = dict_from_row(cursor, user_row)
    
    # Verify password
    if not verify_password(user_credentials.password, user_dict["hashed_password"]):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    cursor.execute("UPDATE users SET last_login = %s WHERE username = %s", 
                  (datetime.utcnow(), user_credentials.username))
    conn.commit()
    conn.close()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict["username"]}, expires_delta=access_token_expires
    )
    
    # Remove password from response
    user_dict.pop('hashed_password', None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user_dict)
    }

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== PATIENT ROUTES ====================

@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient ID already exists
    cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_data.patient_id,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    # Create patient
    patient_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    cursor.execute("""
        INSERT INTO patients (
            id, patient_id, first_name, last_name, date_of_birth, gender,
            phone, email, address, medical_record_number, primary_physician,
            allergies, medications, medical_history, insurance_provider,
            insurance_policy_number, insurance_group_number, consent_given,
            created_at, updated_at, created_by, access_log
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        patient_id, patient_data.patient_id, patient_data.first_name, patient_data.last_name,
        patient_data.date_of_birth, patient_data.gender, patient_data.phone,
        patient_data.email, patient_data.address, patient_data.medical_record_number,
        patient_data.primary_physician, json.dumps(patient_data.allergies),
        json.dumps(patient_data.medications), json.dumps(patient_data.medical_history),
        patient_data.insurance_provider, patient_data.insurance_policy_number,
        patient_data.insurance_group_number, patient_data.consent_given,
        now, now, current_user.id, '[]'
    ))
    
    conn.commit()
    conn.close()
    
    return Patient(**patient_data.dict(), id=patient_id, created_by=current_user.id, created_at=now, updated_at=now)

@api_router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient_row = cursor.fetchone()
    if not patient_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update last accessed
    cursor.execute("UPDATE patients SET last_accessed = %s WHERE id = %s", 
                  (datetime.utcnow(), patient_id))
    conn.commit()
    
    patient_dict = dict_from_row(cursor, patient_row)
    # Convert date fields to strings
    if patient_dict.get('date_of_birth'):
        patient_dict['date_of_birth'] = str(patient_dict['date_of_birth'])
    if patient_dict.get('created_at'):
        patient_dict['created_at'] = patient_dict['created_at'].isoformat() if hasattr(patient_dict['created_at'], 'isoformat') else str(patient_dict['created_at'])
    if patient_dict.get('updated_at'):
        patient_dict['updated_at'] = patient_dict['updated_at'].isoformat() if hasattr(patient_dict['updated_at'], 'isoformat') else str(patient_dict['updated_at'])
    if patient_dict.get('last_accessed'):
        patient_dict['last_accessed'] = patient_dict['last_accessed'].isoformat() if hasattr(patient_dict['last_accessed'], 'isoformat') else str(patient_dict['last_accessed'])
    # Parse JSON fields safely
    patient_dict['allergies'] = json.loads(patient_dict.get('allergies') or '[]')
    patient_dict['medications'] = json.loads(patient_dict.get('medications') or '[]')
    patient_dict['medical_history'] = json.loads(patient_dict.get('medical_history') or '[]')
    patient_dict['access_log'] = json.loads(patient_dict.get('access_log') or '[]')
    
    conn.close()
    
    return Patient(**patient_dict)

@api_router.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(patient_id: str, patient_data: PatientCreate, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = patient_data.dict()
    update_data_json = {
        'first_name': update_data['first_name'],
        'last_name': update_data['last_name'],
        'date_of_birth': update_data['date_of_birth'],
        'gender': update_data['gender'],
        'phone': update_data['phone'],
        'email': update_data['email'],
        'address': update_data['address'],
        'medical_record_number': update_data['medical_record_number'],
        'primary_physician': update_data['primary_physician'],
        'allergies': json.dumps(update_data['allergies']),
        'medications': json.dumps(update_data['medications']),
        'medical_history': json.dumps(update_data['medical_history']),
        'insurance_provider': update_data['insurance_provider'],
        'insurance_policy_number': update_data['insurance_policy_number'],
        'insurance_group_number': update_data['insurance_group_number'],
        'consent_given': update_data['consent_given'],
        'updated_at': datetime.utcnow()
    }

    cursor.execute("""
        UPDATE patients SET first_name = %s, last_name = %s, date_of_birth = %s, gender = %s, 
        phone = %s, email = %s, address = %s, medical_record_number = %s, primary_physician = %s, 
        allergies = %s, medications = %s, medical_history = %s, insurance_provider = %s, 
        insurance_policy_number = %s, insurance_group_number = %s, consent_given = %s, updated_at = %s
        WHERE id = %s
    """, (update_data_json['first_name'], update_data_json['last_name'], update_data_json['date_of_birth'], 
          update_data_json['gender'], update_data_json['phone'], update_data_json['email'], update_data_json['address'],
          update_data_json['medical_record_number'], update_data_json['primary_physician'], update_data_json['allergies'],
          update_data_json['medications'], update_data_json['medical_history'], update_data_json['insurance_provider'],
          update_data_json['insurance_policy_number'], update_data_json['insurance_group_number'], update_data_json['consent_given'], 
          update_data_json['updated_at'], patient_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    updated_patient_row = cursor.fetchone()
    updated_patient_dict = dict_from_row(cursor, updated_patient_row)
    # Convert date fields to strings
    if updated_patient_dict.get('date_of_birth'):
        updated_patient_dict['date_of_birth'] = str(updated_patient_dict['date_of_birth'])
    if updated_patient_dict.get('created_at'):
        updated_patient_dict['created_at'] = updated_patient_dict['created_at'].isoformat() if hasattr(updated_patient_dict['created_at'], 'isoformat') else str(updated_patient_dict['created_at'])
    if updated_patient_dict.get('updated_at'):
        updated_patient_dict['updated_at'] = updated_patient_dict['updated_at'].isoformat() if hasattr(updated_patient_dict['updated_at'], 'isoformat') else str(updated_patient_dict['updated_at'])
    if updated_patient_dict.get('last_accessed'):
        updated_patient_dict['last_accessed'] = updated_patient_dict['last_accessed'].isoformat() if hasattr(updated_patient_dict['last_accessed'], 'isoformat') else str(updated_patient_dict['last_accessed'])
    # Parse JSON fields safely
    updated_patient_dict['allergies'] = json.loads(updated_patient_dict.get('allergies') or '[]')
    updated_patient_dict['medications'] = json.loads(updated_patient_dict.get('medications') or '[]')
    updated_patient_dict['medical_history'] = json.loads(updated_patient_dict.get('medical_history') or '[]')
    updated_patient_dict['access_log'] = json.loads(updated_patient_dict.get('access_log') or '[]')
    
    conn.close()
    return Patient(**updated_patient_dict)

@api_router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Delete patient and associated images
    cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
    cursor.execute("DELETE FROM medical_images WHERE patient_id = %s", (patient_id,))
    conn.commit()
    
    conn.close()
    return {"message": "Patient and related images deleted successfully"}

@api_router.get("/patients", response_model=List[Patient])
async def get_patients(current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients")
    patient_rows = cursor.fetchall()
    
    patients = []
    for row in patient_rows:
        patient_dict = dict_from_row(cursor, row)
        # Convert date fields to strings
        if patient_dict.get('date_of_birth'):
            patient_dict['date_of_birth'] = str(patient_dict['date_of_birth'])
        if patient_dict.get('created_at'):
            patient_dict['created_at'] = patient_dict['created_at'].isoformat() if hasattr(patient_dict['created_at'], 'isoformat') else str(patient_dict['created_at'])
        if patient_dict.get('updated_at'):
            patient_dict['updated_at'] = patient_dict['updated_at'].isoformat() if hasattr(patient_dict['updated_at'], 'isoformat') else str(patient_dict['updated_at'])
        if patient_dict.get('last_accessed'):
            patient_dict['last_accessed'] = patient_dict['last_accessed'].isoformat() if hasattr(patient_dict['last_accessed'], 'isoformat') else str(patient_dict['last_accessed'])
        # Parse JSON fields safely
        patient_dict['allergies'] = json.loads(patient_dict.get('allergies') or '[]')
        patient_dict['medications'] = json.loads(patient_dict.get('medications') or '[]')
        patient_dict['medical_history'] = json.loads(patient_dict.get('medical_history') or '[]')
        patient_dict['access_log'] = json.loads(patient_dict.get('access_log') or '[]')
        patients.append(Patient(**patient_dict))
    
    conn.close()
    return patients

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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")
    
    file_content = await file.read()
    is_dicom = file.filename.lower().endswith('.dcm') or file.content_type == 'application/dicom'
    if is_dicom:
        processed_data = process_dicom_file(file_content)
        image_format = 'DICOM'
    else:
        processed_data = process_standard_image(file_content)
        image_format = file.content_type.split('/')[-1].upper()
    
    # Create medical image record
    image_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO medical_images (
            id, patient_id, study_id, series_id, instance_id, modality,
            body_part, study_date, study_time, institution_name, referring_physician,
            dicom_metadata, image_data, thumbnail_data, original_filename,
            file_size, image_format, window_center, window_width,
            uploaded_at, uploaded_by, access_log
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        image_id, patient_id, study_id, series_id, str(uuid.uuid4()), modality,
        body_part, study_date, study_time, institution_name, referring_physician,
        json.dumps(processed_data['metadata']), processed_data['image_data'], processed_data['thumbnail_data'], file.filename,
        len(file_content), image_format, processed_data['window_center'], processed_data['window_width'],
        datetime.utcnow(), current_user.id, '[]'
    ))
    
    conn.commit()
    conn.close()
    
    return {"message": "Image uploaded successfully", "image_id": image_id}

@api_router.get("/patients/{patient_id}/images", response_model=List[MedicalImage])
async def get_patient_images(patient_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")
    
    cursor.execute("SELECT * FROM medical_images WHERE patient_id = %s", (patient_id,))
    image_rows = cursor.fetchall()
    
    images = []
    for row in image_rows:
        image_dict = dict_from_row(cursor, row)
        # Convert date/time fields to strings
        if image_dict.get('study_date'):
            image_dict['study_date'] = str(image_dict['study_date'])
        if image_dict.get('study_time'):
            image_dict['study_time'] = str(image_dict['study_time'])
        if image_dict.get('uploaded_at'):
            image_dict['uploaded_at'] = image_dict['uploaded_at'].isoformat() if hasattr(image_dict['uploaded_at'], 'isoformat') else str(image_dict['uploaded_at'])
        # Parse JSON fields safely
        image_dict['dicom_metadata'] = json.loads(image_dict.get('dicom_metadata') or '{}')
        image_dict['access_log'] = json.loads(image_dict.get('access_log') or '[]')
        images.append(MedicalImage(**image_dict))
    
    conn.close()
    return images

@api_router.get("/images/{image_id}", response_model=MedicalImage)
async def get_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM medical_images WHERE id = %s", (image_id,))
    image_row = cursor.fetchone()
    if not image_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_dict = dict_from_row(cursor, image_row)
    # Convert date/time fields to strings
    if image_dict.get('study_date'):
        image_dict['study_date'] = str(image_dict['study_date'])
    if image_dict.get('study_time'):
        image_dict['study_time'] = str(image_dict['study_time'])
    if image_dict.get('uploaded_at'):
        image_dict['uploaded_at'] = image_dict['uploaded_at'].isoformat() if hasattr(image_dict['uploaded_at'], 'isoformat') else str(image_dict['uploaded_at'])
    # Parse JSON fields safely
    image_dict['dicom_metadata'] = json.loads(image_dict.get('dicom_metadata') or '{}')
    image_dict['access_log'] = json.loads(image_dict.get('access_log') or '[]')
    
    conn.close()
    return MedicalImage(**image_dict)

@api_router.delete("/images/{image_id}")
async def delete_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM medical_images WHERE id = %s", (image_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Image not found")
    
    cursor.execute("DELETE FROM medical_images WHERE id = %s", (image_id,))
    conn.commit()
    
    conn.close()
    return {"message": "Image deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "PAC System API with MySQL", "status": "running", "database": "MySQL"}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "healthy", 
            "database": "MySQL connected", 
            "users": user_count,
            "config": {
                "host": MYSQL_CONFIG['host'],
                "database": MYSQL_CONFIG['database'],
                "user": MYSQL_CONFIG['user']
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
