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
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import pydicom
import numpy as np
from PIL import Image
import io

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env.sqlite')

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# SQLite database path
DB_PATH = ROOT_DIR.parent / "pac_system.db"

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

# ==================== DATABASE HELPERS ====================

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def dict_from_row(row):
    """Convert SQLite row to dictionary"""
    return dict(row) if row else None

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_dict = dict_from_row(user_row)
    return User(**user_dict)

# ==================== ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (user_data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, user_data.username, user_data.email, user_data.full_name, 
          hashed_password, user_data.role, now))
    
    conn.commit()
    conn.close()
    
    return User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user
    cursor.execute("SELECT * FROM users WHERE username = ?", (user_credentials.username,))
    user_row = cursor.fetchone()
    
    if not user_row or not verify_password(user_credentials.password, user_row["hashed_password"]):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", 
                  (datetime.utcnow().isoformat(), user_credentials.username))
    conn.commit()
    conn.close()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_row["username"]}, expires_delta=access_token_expires
    )
    
    user_dict = dict_from_row(user_row)
    user_dict.pop('hashed_password', None)  # Remove password from response
    
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
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_data.patient_id,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    # Create patient
    patient_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO patients (
            id, patient_id, first_name, last_name, date_of_birth, gender,
            phone, email, address, medical_record_number, primary_physician,
            allergies, medications, medical_history, insurance_provider,
            insurance_policy_number, insurance_group_number, consent_given,
            created_at, updated_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id, patient_data.patient_id, patient_data.first_name, patient_data.last_name,
        patient_data.date_of_birth, patient_data.gender, patient_data.phone,
        patient_data.email, patient_data.address, patient_data.medical_record_number,
        patient_data.primary_physician, json.dumps(patient_data.allergies),
        json.dumps(patient_data.medications), json.dumps(patient_data.medical_history),
        patient_data.insurance_provider, patient_data.insurance_policy_number,
        patient_data.insurance_group_number, patient_data.consent_given,
        now, now, current_user.id
    ))
    
    conn.commit()
    conn.close()
    
    return Patient(**patient_data.dict(), id=patient_id, created_by=current_user.id)

@api_router.get("/patients", response_model=List[Patient])
async def get_patients(current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients")
    patient_rows = cursor.fetchall()
    conn.close()
    
    patients = []
    for row in patient_rows:
        patient_dict = dict_from_row(row)
        # Parse JSON fields
        patient_dict['allergies'] = json.loads(patient_dict.get('allergies', '[]'))
        patient_dict['medications'] = json.loads(patient_dict.get('medications', '[]'))
        patient_dict['medical_history'] = json.loads(patient_dict.get('medical_history', '[]'))
        patient_dict['access_log'] = json.loads(patient_dict.get('access_log', '[]'))
        patients.append(Patient(**patient_dict))
    
    return patients

# Include the router in the main app
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "PAC System API with SQLite", "status": "running"}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        return {"status": "healthy", "database": "connected", "users": user_count}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
