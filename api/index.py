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
        
        # Import the contextlib for lifespan handling
        from contextlib import asynccontextmanager
        
        # Add the backend directory to the path if not already there
        from pathlib import Path
        backend_dir = str(Path(__file__).parent.parent / 'backend')
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        # Mock the lifespan manager to do nothing in serverless mode
        @asynccontextmanager
        async def mock_lifespan(app: FastAPI):
            logger.info("Serverless mode: skipping lifespan events")
            yield
        
        # Create a mock module for the lifespan
        class MockLifespan:
            def __init__(self):
                self.lifespan = mock_lifespan
        
        # Temporarily add mock to modules
        original_modules = sys.modules.copy()
        
        try:
            # Import and patch the backend module
            import server_postgresql_fully_optimized
            
            # Replace the lifespan in the module if it exists
            if hasattr(server_postgresql_fully_optimized, 'lifespan'):
                server_postgresql_fully_optimized.lifespan = mock_lifespan
                logger.info("Patched lifespan function")
            
            # Import the router
            from server_postgresql_fully_optimized import api_router
            
            # Include the full API router
            app.include_router(api_router)
            
            logger.info("Successfully imported backend with clinician_notes support")
            logger.info("Successfully integrated full optimized backend")
            return True
            
        except Exception as inner_e:
            logger.error(f"Error during backend import: {inner_e}")
            # Restore original modules on failure
            sys.modules.clear()
            sys.modules.update(original_modules)
            raise inner_e
        
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
        
        @app.get("/api/patients/{patient_id}/images")
        async def get_patient_images(patient_id: str, current_user = Depends(get_current_user)):
            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                # Check if patient exists
                cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Patient not found")
                
                # Get image metadata including clinician_notes
                cursor.execute("""
                    SELECT id, patient_id, study_id, modality, body_part, study_date,
                           original_filename, uploaded_at, clinician_notes
                    FROM medical_images WHERE patient_id = %s
                    ORDER BY uploaded_at DESC
                """, (patient_id,))
                
                images = []
                for row in cursor.fetchall():
                    image_dict = dict(row)
                    # Convert date/time fields to strings
                    for field in ['study_date', 'uploaded_at']:
                        if image_dict.get(field):
                            if hasattr(image_dict[field], 'isoformat'):
                                image_dict[field] = image_dict[field].isoformat()
                            else:
                                image_dict[field] = str(image_dict[field])
                    images.append(image_dict)
                return images
            finally:
                return_db_connection(conn)
        
        @app.put("/api/images/{image_id}")
        async def update_medical_image(image_id: str, payload: dict, current_user = Depends(get_current_user)):
            """Update medical image fields including clinician_notes."""
            allowed_fields = {"modality", "body_part", "clinician_notes"}
            if not any(k in payload for k in allowed_fields):
                raise HTTPException(status_code=400, detail="No updatable fields provided")

            conn = get_db_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT id, patient_id FROM medical_images WHERE id = %s", (image_id,))
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Image not found")

                updates = []
                params = []

                # Update simple text fields if present
                if 'modality' in payload:
                    updates.append("modality = %s")
                    params.append(payload['modality'])
                if 'body_part' in payload:
                    updates.append("body_part = %s")
                    params.append(payload['body_part'])

                # Update dedicated clinician_notes column only
                if 'clinician_notes' in payload:
                    updates.append("clinician_notes = %s")
                    params.append(payload['clinician_notes'])

                if updates:
                    query = f"UPDATE medical_images SET {', '.join(updates)} WHERE id = %s"
                    params.append(image_id)
                    cursor.execute(query, tuple(params))
                    conn.commit()

                # Insert history entry if notes provided
                if 'clinician_notes' in payload and payload['clinician_notes'] is not None:
                    try:
                        cursor.execute(
                            """
                            INSERT INTO medical_image_notes (id, image_id, user_id, note, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (str(uuid.uuid4()), image_id, current_user['id'], payload['clinician_notes'], datetime.utcnow())
                        )
                        conn.commit()
                    except Exception as e:
                        # History table might not exist yet; log and continue
                        logger.warning(f"Failed to insert into medical_image_notes: {e}")

                return {"message": "Image updated successfully"}
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
        
        # Create default admin user if none exists
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if admin user exists
            cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            if not cursor.fetchone():
                # Create admin user
                admin_id = str(uuid.uuid4())
                admin_password = get_password_hash("password")
                admin_email = "admin@jajuwa.com"
                admin_name = "Administrator"
                now = datetime.utcnow()
                
                cursor.execute("""
                    INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (admin_id, "admin", admin_email, admin_name, admin_password, "admin", now, True))
                
                conn.commit()
                logger.info("Default admin user created: username='admin', password='password'")
            else:
                logger.info("Admin user already exists")
                
            return_db_connection(conn)
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            # Continue anyway - the rest of the API should work
        
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
