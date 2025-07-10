import sys
import os
from pathlib import Path
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Set environment variables for Vercel serverless compatibility
os.environ['USE_MEMORY_CACHE'] = 'true'           # Force memory cache instead of Redis
os.environ['DB_POOL_MIN_CONN'] = '0'              # No connection pooling in serverless
os.environ['DB_POOL_MAX_CONN'] = '1'              # Single connection per request
os.environ['IMAGE_PROCESSING_THREADS'] = '1'      # Single thread for serverless
os.environ['BACKGROUND_TASK_THREADS'] = '1'       # Single thread for serverless
os.environ['CACHE_SIZE'] = '50'                   # Smaller cache for serverless
os.environ['STORAGE_PATH'] = '/tmp'               # Use tmp directory for serverless
os.environ['DISABLE_LIFESPAN'] = 'true'           # Disable lifespan events
os.environ['SERVERLESS_MODE'] = 'true'            # Enable serverless mode

logger.info("Starting PAC System API in serverless mode")

# Mock pillow-heif for Vercel if not available
try:
    import pillow_heif
    logger.info("pillow-heif imported successfully")
except ImportError:
    logger.info("pillow-heif not available, creating mock")
    # Create a mock pillow_heif module
    class MockPillowHeif:
        @staticmethod
        def register_heif_opener():
            pass
    
    sys.modules['pillow_heif'] = MockPillowHeif()

# Mock aioredis if not available (will fallback to memory cache)
try:
    import aioredis
    logger.info("aioredis imported successfully")
except ImportError:
    logger.info("aioredis not available, creating mock")
    # Create a mock aioredis module
    class MockAioredis:
        @staticmethod
        async def from_url(url, **kwargs):
            raise ConnectionError("Redis not available, using memory cache")
        
        @staticmethod
        async def close():
            pass
    
    sys.modules['aioredis'] = MockAioredis()

# Create a simple FastAPI app for serverless deployment
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PAC System API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "PAC System API is running",
        "status": "healthy",
        "mode": "serverless",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "API is operational (serverless mode)",
        "database_url_configured": bool(os.environ.get('DATABASE_URL')),
        "secret_key_configured": bool(os.environ.get('SECRET_KEY'))
    }

@app.get("/api/")
async def api_root():
    return {
        "message": "PAC System API is running",
        "status": "healthy",
        "mode": "serverless",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def api_health_check():
    return {
        "status": "healthy",
        "message": "API is operational (serverless mode)",
        "database_url_configured": bool(os.environ.get('DATABASE_URL')),
        "secret_key_configured": bool(os.environ.get('SECRET_KEY'))
    }

# Import the full optimized backend with error handling
def setup_full_backend():
    """Set up the full backend with all dependencies"""
    try:
        logger.info("Setting up full optimized backend...")
        
        # Import the full optimized backend without the lifespan
        import sys
        
        # First, let's patch the optimized backend to disable lifespan
        original_fastapi = sys.modules.get('fastapi')
        if original_fastapi:
            # Create a patched FastAPI class that ignores lifespan
            class ServerlessFastAPI(original_fastapi.FastAPI):
                def __init__(self, *args, **kwargs):
                    # Remove lifespan from kwargs to prevent startup issues
                    kwargs.pop('lifespan', None)
                    super().__init__(*args, **kwargs)
            
            # Temporarily replace FastAPI in the module
            original_fastapi.FastAPI = ServerlessFastAPI
        
        # Now try to import the backend
        from server_postgresql_fully_optimized import api_router
        
        # Include the full API router
        app.include_router(api_router)
        
        # Restore original FastAPI if we patched it
        if original_fastapi:
            original_fastapi.FastAPI = original_fastapi.FastAPI.__bases__[0]
        
        logger.info("Successfully integrated full optimized backend")
        return True
        
    except ImportError as e:
        logger.error(f"Import error in full backend: {e}")
        return False
    except Exception as e:
        logger.error(f"Error setting up full backend: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# Alternative: Setup minimal backend with essential endpoints
def setup_minimal_backend():
    """Set up minimal backend with essential functionality"""
    try:
        logger.info("Setting up minimal backend...")
        
        # Import essential modules
        import psycopg2
        import psycopg2.extras
        from passlib.context import CryptContext
        from jose import JWTError, jwt
        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPBearer
        from pydantic import BaseModel, EmailStr
        import uuid
        from datetime import datetime, timedelta
        import json
        
        # Configuration
        DATABASE_URL = os.environ.get('DATABASE_URL')
        SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        if not DATABASE_URL:
            logger.error("DATABASE_URL not configured")
            return False
        
        # Setup authentication
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        security = HTTPBearer()
        
        def verify_password(plain_password, hashed_password):
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                return False
        
        def get_password_hash(password):
            return pwd_context.hash(password)
        
        def create_access_token(data: dict, expires_delta: timedelta = None):
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=15)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        
        def get_db_connection():
            return psycopg2.connect(DATABASE_URL)
        
        def return_db_connection(conn):
            if conn:
                conn.close()
        
        async def get_current_user(credentials = Depends(security)):
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
                
                return dict(user_row)
            finally:
                return_db_connection(conn)
        
        # Models
        class UserLogin(BaseModel):
            username: str
            password: str
        
        class UserCreate(BaseModel):
            username: str
            email: EmailStr
            full_name: str
            password: str
            role: str = "user"
        
        # Endpoints
        @app.post("/api/auth/login")
        async def login(user_credentials: UserLogin):
            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT * FROM users WHERE username = %s", (user_credentials.username,))
                user_row = cursor.fetchone()
                
                if not user_row:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                user_dict = dict(user_row)
                
                if not verify_password(user_credentials.password, user_dict["hashed_password"]):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": user_dict["username"]}, expires_delta=access_token_expires
                )
                
                user_dict.pop('hashed_password', None)
                # Convert datetime objects to strings
                for key, value in user_dict.items():
                    if hasattr(value, 'isoformat'):
                        user_dict[key] = value.isoformat()
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": user_dict
                }
            finally:
                return_db_connection(conn)
        
        @app.post("/api/auth/register")
        async def register(user_data: UserCreate):
            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT * FROM users WHERE username = %s", (user_data.username,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Username already registered")
                
                hashed_password = get_password_hash(user_data.password)
                user_id = str(uuid.uuid4())
                now = datetime.utcnow()
                
                cursor.execute("""
                    INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, user_data.username, user_data.email, user_data.full_name, 
                      hashed_password, user_data.role, now))
                
                conn.commit()
                
                return {
                    "id": user_id,
                    "username": user_data.username,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "role": user_data.role,
                    "created_at": now.isoformat()
                }
            finally:
                return_db_connection(conn)
        
        @app.get("/api/patients")
        async def get_patients(current_user = Depends(get_current_user)):
            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 10")
                patients = []
                for row in cursor.fetchall():
                    patient_dict = dict(row)
                    # Convert datetime objects to strings
                    for key, value in patient_dict.items():
                        if hasattr(value, 'isoformat'):
                            patient_dict[key] = value.isoformat()
                        elif isinstance(value, list):
                            patient_dict[key] = value
                    patients.append(patient_dict)
                return patients
            finally:
                return_db_connection(conn)
        
        @app.get("/api/images/{image_id}/thumbnail-base64")
        async def get_thumbnail_base64(image_id: str, current_user = Depends(get_current_user)):
            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT thumbnail_data FROM medical_images WHERE id = %s", (image_id,))
                result = cursor.fetchone()
                
                if not result or not result['thumbnail_data']:
                    raise HTTPException(status_code=404, detail="Thumbnail not found")
                
                return {
                    "thumbnail_data": result['thumbnail_data'],
                    "media_type": "image/webp",
                    "format": "base64"
                }
            finally:
                return_db_connection(conn)
        
        logger.info("Successfully set up minimal backend")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup minimal backend: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# Try full backend first, fallback to minimal
if setup_full_backend():
    logger.info("Full backend integration successful")
elif setup_minimal_backend():
    logger.info("Minimal backend integration successful")
else:
    logger.warning("Using fallback mode - limited functionality")
    
    @app.post("/api/auth/login")
    async def login_fallback():
        return {"error": "Backend not available", "message": "Database connection failed"}
    
    @app.get("/api/patients")
    async def patients_fallback():
        return {"error": "Backend not available", "message": "Database connection failed"}

logger.info("PAC System API initialized successfully")
