from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status, BackgroundTasks
from fastapi.responses import StreamingResponse, Response, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import uuid
import base64
import json
import asyncio
import concurrent.futures
from functools import lru_cache
import threading
import hashlib
import mimetypes
from pathlib import Path
import shutil
import tempfile
import aiofiles
import aioredis
from contextlib import asynccontextmanager

# Database imports
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from dotenv import load_dotenv

# Image processing imports
import pydicom
import numpy as np
from PIL import Image
import io
from pillow_heif import register_heif_opener

# Authentication imports
from passlib.context import CryptContext
from jose import JWTError, jwt

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register HEIF opener for modern image formats (with error handling)
try:
    register_heif_opener()
except Exception as e:
    logger.warning(f"Failed to register HEIF opener: {e}")

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# ==================== CONFIGURATION ====================

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database (Serverless Compatible)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_POOL_MIN_CONN = int(os.environ.get('DB_POOL_MIN_CONN', '0'))  # No pooling for serverless
    DB_POOL_MAX_CONN = int(os.environ.get('DB_POOL_MAX_CONN', '1'))  # Single connection for serverless
    SERVERLESS_MODE = os.environ.get('SERVERLESS_MODE', 'false').lower() == 'true'
    
    # Redis (with Memory Cache Fallback)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    USE_MEMORY_CACHE = os.environ.get('USE_MEMORY_CACHE', 'true').lower() == 'true'
    CACHE_TTL = 3600  # 1 hour
    
    # File Storage (Serverless Compatible)
    STORAGE_PATH = Path(os.environ.get('STORAGE_PATH', '/tmp' if os.environ.get('SERVERLESS_MODE') else './storage'))
    THUMBNAIL_PATH = STORAGE_PATH / 'thumbnails'
    IMAGES_PATH = STORAGE_PATH / 'images'
    
    # Image Processing
    MAX_IMAGE_SIZE = 4096  # Max dimension
    THUMBNAIL_SIZE = (200, 200)
    JPEG_QUALITY = 85
    THUMBNAIL_QUALITY = 75
    WEBP_QUALITY = 80
    
    # Performance (Serverless Compatible)
    IMAGE_PROCESSING_THREADS = int(os.environ.get('IMAGE_PROCESSING_THREADS', '1'))
    BACKGROUND_TASK_THREADS = int(os.environ.get('BACKGROUND_TASK_THREADS', '1'))
    CACHE_SIZE = int(os.environ.get('CACHE_SIZE', '50'))

config = Config()

# Create storage directories (with error handling for serverless)
try:
    config.STORAGE_PATH.mkdir(exist_ok=True)
    config.THUMBNAIL_PATH.mkdir(exist_ok=True)
    config.IMAGES_PATH.mkdir(exist_ok=True)
except Exception as e:
    logger.warning(f"Failed to create storage directories: {e}")
    # In serverless, we'll create directories on-demand

# ==================== GLOBAL INSTANCES ====================

# Thread pools
IMAGE_PROCESSING_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=config.IMAGE_PROCESSING_THREADS,
    thread_name_prefix="image_processing"
)

BACKGROUND_TASK_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=config.BACKGROUND_TASK_THREADS,
    thread_name_prefix="background_tasks"
)

# Database connection pool
db_pool = None
redis_client = None

# In-memory cache fallback (for when Redis is not available)
memory_cache = {}
cache_expiry = {}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ==================== DATABASE CONNECTION POOL ====================

def create_db_pool():
    """Create database connection pool for Supabase (serverless compatible)"""
    global db_pool
    if config.SERVERLESS_MODE:
        logger.info("Serverless mode: skipping connection pool creation")
        return
    try:
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            config.DB_POOL_MIN_CONN,
            config.DB_POOL_MAX_CONN,
            config.DATABASE_URL
        )
        logger.info(f"Supabase database connection pool created successfully (min: {config.DB_POOL_MIN_CONN}, max: {config.DB_POOL_MAX_CONN})")
    except Exception as e:
        logger.error(f"Failed to create Supabase database pool: {e}")
        raise

def get_db_connection():
    """Get database connection (serverless compatible)"""
    global db_pool
    
    # In serverless mode, create direct connections
    if config.SERVERLESS_MODE:
        try:
            conn = psycopg2.connect(config.DATABASE_URL)
            logger.debug("Created direct database connection for serverless")
            return conn
        except Exception as e:
            logger.error(f"Failed to create direct database connection: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Traditional pooled connection
    if db_pool is None:
        create_db_pool()
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def return_db_connection(conn):
    """Return database connection (serverless compatible)"""
    global db_pool
    
    # In serverless mode, close the connection
    if config.SERVERLESS_MODE:
        if conn:
            conn.close()
            logger.debug("Closed direct database connection for serverless")
        return
    
    # Traditional pooled connection
    if db_pool and conn:
        db_pool.putconn(conn)

# ==================== REDIS CACHE ====================

async def get_redis_client():
    """Get Redis client with fallback support"""
    global redis_client
    if not config.USE_MEMORY_CACHE and redis_client is None:
        try:
            # Redis client disabled due to Python 3.11 compatibility issues
            redis_client = None
            logger.info("Redis client disabled due to Python 3.11 compatibility issues")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            redis_client = None
    return redis_client

async def cache_get(key: str) -> Optional[str]:
    """Get value from cache (Redis or Memory)"""
    try:
        if config.USE_MEMORY_CACHE:
            # Use memory cache
            if key in memory_cache:
                # Check if expired
                if key in cache_expiry and datetime.utcnow() > cache_expiry[key]:
                    del memory_cache[key]
                    del cache_expiry[key]
                    return None
                return memory_cache[key]
            return None
        else:
            # Use Redis
            redis = await get_redis_client()
            if redis:
                return await redis.get(key)
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
    return None

async def cache_set(key: str, value: str, ttl: int = config.CACHE_TTL):
    """Set value in cache (Redis or Memory)"""
    try:
        if config.USE_MEMORY_CACHE:
            # Use memory cache
            memory_cache[key] = value
            cache_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
            # Simple cleanup to prevent memory bloat
            if len(memory_cache) > config.CACHE_SIZE:
                await cleanup_memory_cache()
        else:
            # Use Redis
            redis = await get_redis_client()
            if redis:
                await redis.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")

async def cache_delete(key: str):
    """Delete value from cache (Redis or Memory)"""
    try:
        if config.USE_MEMORY_CACHE:
            # Use memory cache
            if key in memory_cache:
                del memory_cache[key]
            if key in cache_expiry:
                del cache_expiry[key]
        else:
            # Use Redis
            redis = await get_redis_client()
            if redis:
                await redis.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete failed: {e}")

async def cleanup_memory_cache():
    """Clean up expired cache entries from memory"""
    try:
        current_time = datetime.utcnow()
        expired_keys = [key for key, expiry in cache_expiry.items() if current_time > expiry]
        for key in expired_keys:
            if key in memory_cache:
                del memory_cache[key]
            del cache_expiry[key]
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    except Exception as e:
        logger.warning(f"Memory cache cleanup failed: {e}")

# ==================== MODELS ====================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    role: str
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
    modality: str
    body_part: str
    study_date: str
    study_time: str
    institution_name: str
    referring_physician: str
    dicom_metadata: Dict[str, Any] = {}
    original_filename: str
    file_size: int
    image_format: str
    window_center: Optional[float] = None
    window_width: Optional[float] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str
    access_log: List[Dict[str, Any]] = []
    
    # For compatibility with existing Supabase schema
    image_data: str = ""  # Will be empty when using file storage
    thumbnail_data: str = ""  # Will be empty when using file storage

class MedicalImageThumbnail(BaseModel):
    id: str
    patient_id: str
    study_id: str
    modality: str
    body_part: str
    study_date: str
    original_filename: str
    uploaded_at: datetime

# ==================== EXAMINATION MODELS ====================

class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    model: str
    manufacturer: str
    device_type: str  # 'CT', 'MRI', 'X-Ray', 'Ultrasound', 'PET', 'SPECT', etc.
    serial_number: Optional[str] = None
    installation_date: Optional[str] = None
    last_calibration: Optional[str] = None
    status: str = "active"  # 'active', 'maintenance', 'inactive'
    location: str  # Department or room location
    specifications: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DeviceCreate(BaseModel):
    name: str
    model: str
    manufacturer: str
    device_type: str
    serial_number: Optional[str] = None
    installation_date: Optional[str] = None
    last_calibration: Optional[str] = None
    status: str = "active"
    location: str
    specifications: Dict[str, Any] = {}

class Examination(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    examination_type: str  # 'CT Scan', 'MRI', 'X-Ray', 'Ultrasound', etc.
    examination_date: str
    examination_time: str
    device_id: str  # Reference to the device used
    device_name: str  # Device name for quick access
    referring_physician: str
    performing_physician: str
    body_part_examined: str
    clinical_indication: str  # Reason for examination
    examination_protocol: str  # Protocol used
    contrast_agent: Optional[str] = None
    contrast_amount: Optional[str] = None
    patient_position: Optional[str] = None
    radiation_dose: Optional[str] = None  # For X-ray, CT
    image_count: int = 0  # Number of images in this examination
    status: str = "completed"  # 'pending', 'in_progress', 'completed', 'reported', 'archived'
    priority: str = "normal"  # 'urgent', 'high', 'normal', 'low'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    # HIPAA Compliance
    access_log: List[Dict[str, Any]] = []

class ExaminationCreate(BaseModel):
    patient_id: str
    examination_type: str
    examination_date: str
    examination_time: str
    device_id: str
    referring_physician: str
    performing_physician: str
    body_part_examined: str
    clinical_indication: str
    examination_protocol: str
    contrast_agent: Optional[str] = None
    contrast_amount: Optional[str] = None
    patient_position: Optional[str] = None
    radiation_dose: Optional[str] = None
    priority: str = "normal"

class ExaminationReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    examination_id: str
    report_type: str  # 'preliminary', 'final', 'addendum'
    report_status: str  # 'draft', 'pending', 'approved', 'signed'
    findings: str  # Main findings
    impression: str  # Clinical impression
    recommendations: str  # Recommendations
    report_date: str
    report_time: str
    reporting_physician: str
    dictated_by: Optional[str] = None
    transcribed_by: Optional[str] = None
    verified_by: Optional[str] = None
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    technical_quality: str = "adequate"  # 'excellent', 'good', 'adequate', 'poor'
    limitations: Optional[str] = None
    comparison_studies: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    # HIPAA Compliance
    access_log: List[Dict[str, Any]] = []

class ExaminationReportCreate(BaseModel):
    examination_id: str
    report_type: str = "final"
    findings: str
    impression: str
    recommendations: str
    report_date: str
    report_time: str
    reporting_physician: str
    dictated_by: Optional[str] = None
    transcribed_by: Optional[str] = None
    technical_quality: str = "adequate"
    limitations: Optional[str] = None
    comparison_studies: Optional[str] = None

class ExaminationWithDetails(BaseModel):
    """Examination with associated device info and image count"""
    id: str
    patient_id: str
    examination_type: str
    examination_date: str
    examination_time: str
    device_id: str
    device_name: str
    device_model: str
    device_manufacturer: str
    device_type: str
    device_location: str
    referring_physician: str
    performing_physician: str
    body_part_examined: str
    clinical_indication: str
    examination_protocol: str
    contrast_agent: Optional[str] = None
    image_count: int = 0
    status: str
    priority: str
    created_at: datetime
    has_reports: bool = False
    report_count: int = 0

# ==================== FILE STORAGE ====================

class FileStorageManager:
    @staticmethod
    def get_image_path(image_id: str, format: str) -> Path:
        """Get image file path"""
        return config.IMAGES_PATH / f"{image_id}.{format.lower()}"
    
    @staticmethod
    def get_thumbnail_path(image_id: str) -> Path:
        """Get thumbnail file path"""
        return config.THUMBNAIL_PATH / f"{image_id}_thumb.webp"
    
    @staticmethod
    async def save_image(image_data: bytes, image_id: str, format: str) -> str:
        """Save image to disk"""
        image_path = FileStorageManager.get_image_path(image_id, format)
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(image_data)
        return str(image_path)
    
    @staticmethod
    async def save_thumbnail(thumbnail_data: bytes, image_id: str) -> str:
        """Save thumbnail to disk"""
        thumbnail_path = FileStorageManager.get_thumbnail_path(image_id)
        async with aiofiles.open(thumbnail_path, 'wb') as f:
            await f.write(thumbnail_data)
        return str(thumbnail_path)
    
    @staticmethod
    async def delete_image_files(image_id: str, format: str):
        """Delete image files from disk"""
        try:
            image_path = FileStorageManager.get_image_path(image_id, format)
            thumbnail_path = FileStorageManager.get_thumbnail_path(image_id)
            
            if image_path.exists():
                image_path.unlink()
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete image files: {e}")

# ==================== OPTIMIZED IMAGE PROCESSING ====================

@lru_cache(maxsize=config.CACHE_SIZE)
def get_dicom_metadata_cached(metadata_hash: str) -> Dict[str, Any]:
    """Cache DICOM metadata parsing"""
    return {}

class OptimizedImageProcessor:
    @staticmethod
    def process_dicom_file(file_content: bytes) -> Dict[str, Any]:
        """Optimized DICOM file processing"""
        try:
            ds = pydicom.dcmread(io.BytesIO(file_content), force=True)
            
            # Extract essential metadata only
            metadata = {}
            essential_tags = [
                'PatientName', 'PatientID', 'StudyDate', 'StudyTime',
                'Modality', 'BodyPartExamined', 'StudyDescription',
                'SeriesDescription', 'ImageType', 'SliceThickness',
                'WindowCenter', 'WindowWidth'
            ]
            
            for tag_name in essential_tags:
                if hasattr(ds, tag_name):
                    try:
                        value = getattr(ds, tag_name)
                        metadata[tag_name] = str(value)
                    except:
                        pass
            
            # Process image data
            if hasattr(ds, 'pixel_array'):
                try:
                    pixel_array = ds.pixel_array
                    
                    # Handle multi-dimensional arrays
                    if len(pixel_array.shape) == 3:
                        if pixel_array.shape[2] == 3:  # RGB
                            pixel_array = np.average(pixel_array, axis=2, weights=[0.299, 0.587, 0.114])
                        else:
                            pixel_array = pixel_array[:, :, 0]
                    
                    # Apply windowing
                    window_center = getattr(ds, 'WindowCenter', None)
                    window_width = getattr(ds, 'WindowWidth', None)
                    
                    if window_center and window_width:
                        if isinstance(window_center, (list, tuple)):
                            window_center = float(window_center[0])
                        else:
                            window_center = float(window_center)
                            
                        if isinstance(window_width, (list, tuple)):
                            window_width = float(window_width[0])
                        else:
                            window_width = float(window_width)
                        
                        img_min = window_center - window_width / 2
                        img_max = window_center + window_width / 2
                        pixel_array = np.clip(pixel_array, img_min, img_max)
                    
                    # Normalize efficiently
                    pixel_min, pixel_max = pixel_array.min(), pixel_array.max()
                    if pixel_max != pixel_min:
                        pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                    else:
                        pixel_array = np.full_like(pixel_array, 128, dtype=np.uint8)
                    
                    # Create PIL image
                    image = Image.fromarray(pixel_array, mode='L')
                    
                    # Resize if too large
                    if max(image.size) > config.MAX_IMAGE_SIZE:
                        image.thumbnail((config.MAX_IMAGE_SIZE, config.MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
                    
                    # Create thumbnail
                    thumbnail = image.copy()
                    thumbnail.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    
                    # Save as WebP for better compression
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='WebP', quality=config.WEBP_QUALITY)
                    image_data = img_buffer.getvalue()
                    
                    thumb_buffer = io.BytesIO()
                    thumbnail.save(thumb_buffer, format='WebP', quality=config.THUMBNAIL_QUALITY)
                    thumbnail_data = thumb_buffer.getvalue()
                    
                    return {
                        'metadata': metadata,
                        'image_data': image_data,
                        'thumbnail_data': thumbnail_data,
                        'window_center': float(window_center) if window_center else None,
                        'window_width': float(window_width) if window_width else None,
                        'format': 'webp'
                    }
                    
                except Exception as img_error:
                    logger.error(f"Error processing DICOM pixel array: {str(img_error)}")
                    return {
                        'metadata': metadata,
                        'image_data': None,
                        'thumbnail_data': None,
                        'window_center': None,
                        'window_width': None,
                        'format': 'webp'
                    }
            
            return {
                'metadata': metadata,
                'image_data': None,
                'thumbnail_data': None,
                'window_center': None,
                'window_width': None,
                'format': 'webp'
            }
            
        except Exception as e:
            logger.error(f"Error processing DICOM file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing DICOM file: {str(e)}")
    
    @staticmethod
    def process_standard_image(file_content: bytes) -> Dict[str, Any]:
        """Optimized standard image processing"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Resize if too large
            if max(image.size) > config.MAX_IMAGE_SIZE:
                image.thumbnail((config.MAX_IMAGE_SIZE, config.MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            
            # Create thumbnail
            thumbnail = image.copy()
            thumbnail.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            # Save as WebP for better compression
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='WebP', quality=config.WEBP_QUALITY)
            image_data = img_buffer.getvalue()
            
            thumb_buffer = io.BytesIO()
            thumbnail.save(thumb_buffer, format='WebP', quality=config.THUMBNAIL_QUALITY)
            thumbnail_data = thumb_buffer.getvalue()
            
            return {
                'metadata': {},
                'image_data': image_data,
                'thumbnail_data': thumbnail_data,
                'window_center': None,
                'window_width': None,
                'format': 'webp'
            }
            
        except Exception as e:
            logger.error(f"Error processing image file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing image file: {str(e)}")

# ==================== ASYNC PROCESSING ====================

async def process_image_async(file_content: bytes, is_dicom: bool) -> Dict[str, Any]:
    """Asynchronous image processing"""
    loop = asyncio.get_event_loop()
    
    if is_dicom:
        return await loop.run_in_executor(
            IMAGE_PROCESSING_POOL,
            OptimizedImageProcessor.process_dicom_file,
            file_content
        )
    else:
        return await loop.run_in_executor(
            IMAGE_PROCESSING_POOL,
            OptimizedImageProcessor.process_standard_image,
            file_content
        )

# ==================== AUTHENTICATION ====================

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return hashed_password == plain_password

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Check cache first
    cache_key = f"user:{credentials.credentials}"
    cached_user = await cache_get(cache_key)
    
    if cached_user:
        return User(**json.loads(cached_user))
    
    try:
        payload = jwt.decode(credentials.credentials, config.SECRET_KEY, algorithms=[config.ALGORITHM])
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
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()
        
        if user_row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_dict = dict(user_row)
        user = User(**user_dict)
        
        # Cache user for 15 minutes
        await cache_set(cache_key, user.json(), 900)
        
        return user
    finally:
        return_db_connection(conn)

# ==================== FASTAPI APP ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_pool()
    await get_redis_client()
    yield
    # Shutdown
    if db_pool:
        db_pool.closeall()
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="PAC System API - Fully Optimized",
    version="2.0.0",
    lifespan=lifespan
)

api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== OPTIMIZED ROUTES ====================

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (user_data.username,))
        if cursor.fetchone():
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
        
        return User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            created_at=now
        )
    finally:
        return_db_connection(conn)

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Find user
        cursor.execute("SELECT * FROM users WHERE username = %s", (user_credentials.username,))
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_dict = dict(user_row)
        
        # Verify password
        if not verify_password(user_credentials.password, user_dict["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        cursor.execute("UPDATE users SET last_login = %s WHERE username = %s", 
                      (datetime.utcnow(), user_credentials.username))
        conn.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    finally:
        return_db_connection(conn)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate, current_user: User = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if patient ID already exists
        cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_data.patient_id,))
        if cursor.fetchone():
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
        
        # Clear cache
        await cache_delete("patients:all")
        
        return Patient(**patient_data.dict(), id=patient_id, created_by=current_user.id, created_at=now, updated_at=now)
    finally:
        return_db_connection(conn)

@api_router.get("/patients", response_model=List[Patient])
async def get_patients(current_user: User = Depends(get_current_user)):
    # Check cache first
    cached_patients = await cache_get("patients:all")
    if cached_patients:
        return [Patient(**p) for p in json.loads(cached_patients)]
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM patients")
        patient_rows = cursor.fetchall()
        
        patients = []
        for row in patient_rows:
            patient_dict = dict(row)
            # Convert date fields to strings
            for field in ['date_of_birth', 'created_at', 'updated_at', 'last_accessed']:
                if patient_dict.get(field):
                    if hasattr(patient_dict[field], 'isoformat'):
                        patient_dict[field] = patient_dict[field].isoformat()
                    else:
                        patient_dict[field] = str(patient_dict[field])
            
            # Parse JSON fields safely
            for field in ['allergies', 'medications', 'medical_history', 'access_log']:
                patient_dict[field] = json.loads(patient_dict.get(field) or '[]')
            
            patients.append(Patient(**patient_dict))
        
        # Cache for 30 minutes
        await cache_set("patients:all", json.dumps([p.dict() for p in patients], default=str), 1800)
        
        return patients
    finally:
        return_db_connection(conn)

@api_router.post("/patients/{patient_id}/images")
async def upload_medical_image(
    patient_id: str,
    background_tasks: BackgroundTasks,
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
    """Optimized image upload with file storage and async processing"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if patient exists
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        
        file_content = await file.read()
        is_dicom = file.filename.lower().endswith('.dcm') or file.content_type == 'application/dicom'
        
        # Process image asynchronously
        processed_data = await process_image_async(file_content, is_dicom)
        
        image_format = 'DICOM' if is_dicom else file.content_type.split('/')[-1].upper()
        image_id = str(uuid.uuid4())
        
        # Save files to disk
        image_path = None
        thumbnail_path = None
        
        if processed_data['image_data']:
            image_path = await FileStorageManager.save_image(
                processed_data['image_data'], image_id, processed_data['format']
            )
        
        if processed_data['thumbnail_data']:
            thumbnail_path = await FileStorageManager.save_thumbnail(
                processed_data['thumbnail_data'], image_id
            )
        
        # Store image data both in files and database (for Supabase compatibility)
        image_data_b64 = ""
        thumbnail_data_b64 = ""
        
        if processed_data['image_data']:
            # Also store in database for compatibility
            image_data_b64 = base64.b64encode(processed_data['image_data']).decode()
        
        if processed_data['thumbnail_data']:
            # Also store in database for compatibility
            thumbnail_data_b64 = base64.b64encode(processed_data['thumbnail_data']).decode()
        
        # Create medical image record using existing Supabase schema
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
            json.dumps(processed_data['metadata']), image_data_b64, thumbnail_data_b64, file.filename,
            len(file_content), image_format, processed_data['window_center'], processed_data['window_width'],
            datetime.utcnow(), current_user.id, '[]'
        ))
        
        conn.commit()
        
        # Clear cache
        await cache_delete(f"patient:{patient_id}:images")
        
        # Add background task for additional processing if needed
        background_tasks.add_task(log_image_upload, image_id, current_user.id)
        
        return {"message": "Image uploaded successfully", "image_id": image_id}
    finally:
        return_db_connection(conn)

@api_router.get("/patients/{patient_id}/images", response_model=List[MedicalImageThumbnail])
async def get_patient_images(patient_id: str, current_user: User = Depends(get_current_user)):
    """Get patient images with progressive loading (thumbnails first)"""
    # Check cache first
    cache_key = f"patient:{patient_id}:images"
    cached_images = await cache_get(cache_key)
    if cached_images:
        return [MedicalImageThumbnail(**img) for img in json.loads(cached_images)]
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if patient exists
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get image metadata only (no binary data)
        cursor.execute("""
            SELECT id, patient_id, study_id, modality, body_part, study_date,
                   original_filename, uploaded_at
            FROM medical_images WHERE patient_id = %s
            ORDER BY uploaded_at DESC
        """, (patient_id,))
        
        image_rows = cursor.fetchall()
        
        images = []
        for row in image_rows:
            image_dict = dict(row)
            # Convert date/time fields to strings
            for field in ['study_date', 'uploaded_at']:
                if image_dict.get(field):
                    if hasattr(image_dict[field], 'isoformat'):
                        image_dict[field] = image_dict[field].isoformat()
                    else:
                        image_dict[field] = str(image_dict[field])
            images.append(MedicalImageThumbnail(**image_dict))
        
        # Cache for 10 minutes
        await cache_set(cache_key, json.dumps([img.dict() for img in images], default=str), 600)
        
        return images
    finally:
        return_db_connection(conn)

@api_router.get("/images/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: str, current_user: User = Depends(get_current_user)):
    """Serve thumbnail with file-first approach (Supabase compatible)"""
    # Try to serve from file first (fastest)
    thumbnail_path = FileStorageManager.get_thumbnail_path(image_id)
    if thumbnail_path.exists():
        return FileResponse(
            thumbnail_path,
            media_type="image/webp",
            headers={"Cache-Control": "max-age=3600"}
        )
    
    # Fallback to database (Supabase compatibility)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT thumbnail_data FROM medical_images WHERE id = %s", (image_id,))
        result = cursor.fetchone()
        
        if not result or not result['thumbnail_data']:
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        thumbnail_data = base64.b64decode(result['thumbnail_data'])
        
        # Save to file for future requests
        await FileStorageManager.save_thumbnail(thumbnail_data, image_id)
        
        return Response(
            content=thumbnail_data,
            media_type="image/webp",
            headers={"Cache-Control": "max-age=3600"}
        )
    finally:
        return_db_connection(conn)

@api_router.get("/images/{image_id}/thumbnail-base64")
async def get_image_thumbnail_base64(image_id: str, current_user: User = Depends(get_current_user)):
    """Serve thumbnail as base64 JSON (for production/remote backend compatibility)"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT thumbnail_data FROM medical_images WHERE id = %s", (image_id,))
        result = cursor.fetchone()
        
        if not result or not result['thumbnail_data']:
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        thumbnail_data_base64 = result['thumbnail_data']
        
        # Detect format from base64 data
        try:
            first_bytes = base64.b64decode(thumbnail_data_base64[:20])
            media_type = "image/webp"  # Default for optimized backend
            if first_bytes.startswith(b'\x89PNG'):
                media_type = "image/png"
            elif first_bytes.startswith(b'\xff\xd8\xff'):
                media_type = "image/jpeg"
            elif first_bytes.startswith(b'GIF87a') or first_bytes.startswith(b'GIF89a'):
                media_type = "image/gif"
            elif first_bytes.startswith(b'RIFF'):
                media_type = "image/webp"
        except:
            media_type = "image/webp"
        
        return {
            "thumbnail_data": thumbnail_data_base64,
            "media_type": media_type,
            "format": "base64"
        }
    finally:
        return_db_connection(conn)

@api_router.get("/images/{image_id}/data")
async def get_image_data(image_id: str, current_user: User = Depends(get_current_user)):
    """Serve full image with file-first approach (Supabase compatible)"""
    # Try to serve from file first (fastest)
    image_path = FileStorageManager.get_image_path(image_id, 'webp')
    if image_path.exists():
        return FileResponse(
            image_path,
            media_type="image/webp",
            headers={"Cache-Control": "max-age=3600"}
        )
    
    # Fallback to database (Supabase compatibility)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT image_data, image_format FROM medical_images WHERE id = %s", (image_id,))
        result = cursor.fetchone()
        
        if not result or not result['image_data']:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_data = base64.b64decode(result['image_data'])
        
        # Save to file for future requests
        await FileStorageManager.save_image(image_data, image_id, 'webp')
        
        # Determine media type
        media_type = "image/webp"
        if result['image_format'] and result['image_format'].upper() == 'DICOM':
            media_type = "application/dicom"
        
        return Response(
            content=image_data,
            media_type=media_type,
            headers={"Cache-Control": "max-age=3600"}
        )
    finally:
        return_db_connection(conn)

@api_router.get("/images/{image_id}", response_model=MedicalImage)
async def get_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    """Get image metadata"""
    # Check cache first
    cache_key = f"image_metadata:{image_id}"
    cached_metadata = await cache_get(cache_key)
    if cached_metadata:
        return MedicalImage(**json.loads(cached_metadata))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM medical_images WHERE id = %s", (image_id,))
        image_row = cursor.fetchone()
        
        if not image_row:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_dict = dict(image_row)
        
        # Convert date/time fields to strings
        for field in ['study_date', 'study_time', 'uploaded_at']:
            if image_dict.get(field):
                if hasattr(image_dict[field], 'isoformat'):
                    image_dict[field] = image_dict[field].isoformat()
                else:
                    image_dict[field] = str(image_dict[field])
        
        # Parse JSON fields safely
        image_dict['dicom_metadata'] = json.loads(image_dict.get('dicom_metadata') or '{}')
        image_dict['access_log'] = json.loads(image_dict.get('access_log') or '[]')
        
        image = MedicalImage(**image_dict)
        
        # Cache for 1 hour
        await cache_set(cache_key, image.json(), 3600)
        
        return image
    finally:
        return_db_connection(conn)

@api_router.delete("/images/{image_id}")
async def delete_medical_image(image_id: str, current_user: User = Depends(get_current_user)):
    """Delete medical image"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get image info before deletion
        cursor.execute("SELECT image_format, patient_id FROM medical_images WHERE id = %s", (image_id,))
        image_info = cursor.fetchone()
        
        if not image_info:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete from database
        cursor.execute("DELETE FROM medical_images WHERE id = %s", (image_id,))
        conn.commit()
        
        # Delete files from disk (if they exist)
        try:
            image_path = FileStorageManager.get_image_path(image_id, 'webp')
            thumbnail_path = FileStorageManager.get_thumbnail_path(image_id)
            
            if image_path.exists():
                image_path.unlink()
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete image files: {e}")
        
        # Clear cache
        await cache_delete(f"image:{image_id}")
        await cache_delete(f"thumbnail:{image_id}")
        await cache_delete(f"image_metadata:{image_id}")
        await cache_delete(f"patient:{image_info['patient_id']}:images")
        
        return {"message": "Image deleted successfully"}
    finally:
        return_db_connection(conn)

# ==================== EXAMINATION MANAGEMENT ENDPOINTS ====================

@api_router.post("/devices", response_model=Device)
async def create_device(device_data: DeviceCreate, current_user: User = Depends(get_current_user)):
    """Create a new medical device"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Create device
        device_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO devices (id, name, model, manufacturer, device_type, serial_number, 
                               installation_date, last_calibration, status, location, specifications, 
                               created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            device_id, device_data.name, device_data.model, device_data.manufacturer,
            device_data.device_type, device_data.serial_number, device_data.installation_date,
            device_data.last_calibration, device_data.status, device_data.location,
            json.dumps(device_data.specifications), datetime.utcnow(), datetime.utcnow()
        ))
        
        # Get the created device
        cursor.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
        device_record = cursor.fetchone()
        
        conn.commit()
        
        device = Device(**dict(device_record))
        logger.info(f"Device created: {device.name} by user {current_user.id}")
        
        return device
    finally:
        return_db_connection(conn)

@api_router.get("/devices", response_model=List[Device])
async def get_devices(current_user: User = Depends(get_current_user)):
    """Get all medical devices"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM devices ORDER BY name")
        devices = cursor.fetchall()
        
        return [Device(**dict(device)) for device in devices]
    finally:
        return_db_connection(conn)

@api_router.post("/examinations", response_model=Examination)
async def create_examination(examination_data: ExaminationCreate, current_user: User = Depends(get_current_user)):
    """Create a new examination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get device name for quick access
        cursor.execute("SELECT name FROM devices WHERE id = %s", (examination_data.device_id,))
        device_record = cursor.fetchone()
        if not device_record:
            raise HTTPException(status_code=404, detail="Device not found")
        device_name = device_record['name']
        
        # Create examination
        examination_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO examinations (id, patient_id, examination_type, examination_date, 
                                    examination_time, device_id, device_name, referring_physician, 
                                    performing_physician, body_part_examined, clinical_indication,
                                    examination_protocol, contrast_agent, contrast_amount, 
                                    patient_position, radiation_dose, priority, created_at, 
                                    updated_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            examination_id, examination_data.patient_id, examination_data.examination_type,
            examination_data.examination_date, examination_data.examination_time,
            examination_data.device_id, device_name, examination_data.referring_physician,
            examination_data.performing_physician, examination_data.body_part_examined,
            examination_data.clinical_indication, examination_data.examination_protocol,
            examination_data.contrast_agent, examination_data.contrast_amount,
            examination_data.patient_position, examination_data.radiation_dose,
            examination_data.priority, datetime.utcnow(), datetime.utcnow(), current_user.id
        ))
        
        # Get the created examination
        cursor.execute("SELECT * FROM examinations WHERE id = %s", (examination_id,))
        examination_record = cursor.fetchone()
        
        conn.commit()
        
        examination = Examination(**dict(examination_record))
        logger.info(f"Examination created: {examination.examination_type} for patient {examination.patient_id}")
        
        return examination
    finally:
        return_db_connection(conn)

@api_router.get("/patients/{patient_id}/examinations", response_model=List[ExaminationWithDetails])
async def get_patient_examinations(patient_id: str, current_user: User = Depends(get_current_user)):
    """Get all examinations for a specific patient"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get examinations with device details and counts
        cursor.execute("""
            SELECT e.*, d.model as device_model, d.manufacturer as device_manufacturer,
                   d.device_type, d.location as device_location,
                   COALESCE(img_count.count, 0) as image_count,
                   COALESCE(report_count.count, 0) as report_count,
                   CASE WHEN report_count.count > 0 THEN true ELSE false END as has_reports
            FROM examinations e
            LEFT JOIN devices d ON e.device_id = d.id
            LEFT JOIN (
                SELECT study_id, COUNT(*) as count 
                FROM medical_images 
                WHERE patient_id = %s 
                GROUP BY study_id
            ) img_count ON e.id = img_count.study_id
            LEFT JOIN (
                SELECT examination_id, COUNT(*) as count 
                FROM examination_reports 
                GROUP BY examination_id
            ) report_count ON e.id = report_count.examination_id
            WHERE e.patient_id = %s
            ORDER BY e.examination_date DESC, e.examination_time DESC
        """, (patient_id, patient_id))
        
        examinations = cursor.fetchall()
        
        # Log access
        access_log = {
            "action": "view_patient_examinations",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "patient_id": patient_id
        }
        
        return [ExaminationWithDetails(**dict(exam)) for exam in examinations]
    finally:
        return_db_connection(conn)

@api_router.get("/examinations/{examination_id}", response_model=Examination)
async def get_examination(examination_id: str, current_user: User = Depends(get_current_user)):
    """Get specific examination details"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM examinations WHERE id = %s", (examination_id,))
        examination_record = cursor.fetchone()
        
        if not examination_record:
            raise HTTPException(status_code=404, detail="Examination not found")
        
        examination = Examination(**dict(examination_record))
        
        # Log access
        access_log = {
            "action": "view_examination",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "examination_id": examination_id
        }
        
        return examination
    finally:
        return_db_connection(conn)

@api_router.get("/examinations/{examination_id}/images", response_model=List[MedicalImageThumbnail])
async def get_examination_images(examination_id: str, current_user: User = Depends(get_current_user)):
    """Get all images for a specific examination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get images for this examination (using study_id as examination_id)
        cursor.execute("""
            SELECT id, patient_id, study_id, modality, body_part, 
                   study_date, original_filename, uploaded_at
            FROM medical_images 
            WHERE study_id = %s 
            ORDER BY uploaded_at DESC
        """, (examination_id,))
        
        images = cursor.fetchall()
        
        # Log access
        access_log = {
            "action": "view_examination_images",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "examination_id": examination_id
        }
        
        return [MedicalImageThumbnail(**dict(img)) for img in images]
    finally:
        return_db_connection(conn)

@api_router.post("/examinations/{examination_id}/reports", response_model=ExaminationReport)
async def create_examination_report(examination_id: str, report_data: ExaminationReportCreate, current_user: User = Depends(get_current_user)):
    """Create a report for an examination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verify examination exists
        cursor.execute("SELECT id FROM examinations WHERE id = %s", (examination_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Examination not found")
        
        # Create report
        report_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO examination_reports (id, examination_id, report_type, report_status, 
                                           findings, impression, recommendations, report_date, 
                                           report_time, reporting_physician, dictated_by, 
                                           transcribed_by, technical_quality, limitations, 
                                           comparison_studies, created_at, updated_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            report_id, examination_id, report_data.report_type, "draft",
            report_data.findings, report_data.impression, report_data.recommendations,
            report_data.report_date, report_data.report_time, report_data.reporting_physician,
            report_data.dictated_by, report_data.transcribed_by, report_data.technical_quality,
            report_data.limitations, report_data.comparison_studies, datetime.utcnow(),
            datetime.utcnow(), current_user.id
        ))
        
        # Get the created report
        cursor.execute("SELECT * FROM examination_reports WHERE id = %s", (report_id,))
        report_record = cursor.fetchone()
        
        conn.commit()
        
        report = ExaminationReport(**dict(report_record))
        logger.info(f"Report created for examination {examination_id} by user {current_user.id}")
        
        return report
    finally:
        return_db_connection(conn)

@api_router.get("/examinations/{examination_id}/reports", response_model=List[ExaminationReport])
async def get_examination_reports(examination_id: str, current_user: User = Depends(get_current_user)):
    """Get all reports for an examination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT * FROM examination_reports 
            WHERE examination_id = %s 
            ORDER BY created_at DESC
        """, (examination_id,))
        
        reports = cursor.fetchall()
        
        # Log access
        access_log = {
            "action": "view_examination_reports",
            "user_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "examination_id": examination_id
        }
        
        return [ExaminationReport(**dict(report)) for report in reports]
    finally:
        return_db_connection(conn)

# ==================== BACKGROUND TASKS ====================

async def log_image_upload(image_id: str, user_id: str):
    """Background task to log image upload"""
    logger.info(f"Image {image_id} uploaded by user {user_id}")

# ==================== HEALTH AND STATUS ====================

@app.get("/")
async def root():
    return {
        "message": "PAC System API - Supabase Optimized",
        "status": "running",
        "version": "2.0.0",
        "database": "Supabase PostgreSQL with Connection Pool",
        "cache": "Redis with Memory Fallback" if not config.USE_MEMORY_CACHE else "In-Memory Cache",
        "storage": "Hybrid (File System + Database)"
    }

@app.get("/health")
async def health_check():
    try:
        # Check database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        finally:
            return_db_connection(conn)
        
        # Check cache status
        if config.USE_MEMORY_CACHE:
            cache_status = f"Memory cache - {len(memory_cache)} entries"
        else:
            redis_status = "connected" if await get_redis_client() else "disconnected"
            cache_status = f"Redis {redis_status}"
        
        # Check storage
        storage_status = "ok" if config.STORAGE_PATH.exists() else "error"
        
        return {
            "status": "healthy",
            "database": f"Supabase PostgreSQL connected - {user_count} users",
            "cache": cache_status,
            "storage": f"Hybrid storage {storage_status}",
            "pool_status": {
                "min_connections": config.DB_POOL_MIN_CONN,
                "max_connections": config.DB_POOL_MAX_CONN
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Include the router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
