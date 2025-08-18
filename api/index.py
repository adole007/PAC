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

# Mock pydicom if not available (for medical image processing)
try:
    import pydicom
    logger.info("pydicom imported successfully")
except ImportError:
    logger.info("pydicom not available, creating mock")
    # Create a mock pydicom module
    class MockPydicom:
        @staticmethod
        def read_file(filename):
            raise Exception("pydicom not available")
        
        class dataset:
            def __init__(self):
                pass
    
    sys.modules['pydicom'] = MockPydicom()

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

@app.get("/api/debug/backend-status")
async def debug_backend_status():
    """Debug endpoint to check which backend is loaded and working"""
    return {
        "backend_type": "minimal" if 'setup_minimal_backend_success' in globals() else "unknown",
        "full_backend_attempted": 'full_backend_attempted' in globals(),
        "full_backend_success": 'full_backend_success' in globals(),
        "minimal_backend_success": 'setup_minimal_backend_success' in globals(),
        "available_endpoints": [route.path for route in app.routes if hasattr(route, 'path')],
        "environment_vars": {
            "DATABASE_URL_configured": bool(os.environ.get('DATABASE_URL')),
            "SECRET_KEY_configured": bool(os.environ.get('SECRET_KEY')),
            "SERVERLESS_MODE": os.environ.get('SERVERLESS_MODE'),
            "USE_MEMORY_CACHE": os.environ.get('USE_MEMORY_CACHE')
        }
    }

@app.get("/api/debug/database")
async def debug_database():
    """Debug endpoint to check database connectivity and table structure"""
    import psycopg2
    import psycopg2.extras
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        return {"error": "DATABASE_URL not configured"}
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if users table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'users'
        """)
        users_table_exists = cursor.fetchone() is not None
        
        # Check if patients table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'patients'
        """)
        patients_table_exists = cursor.fetchone() is not None
        
        # Count users if table exists
        user_count = 0
        if users_table_exists:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        
        # Count patients if table exists
        patient_count = 0
        if patients_table_exists:
            cursor.execute("SELECT COUNT(*) FROM patients")
            patient_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "database_connected": True,
            "users_table_exists": users_table_exists,
            "patients_table_exists": patients_table_exists,
            "user_count": user_count,
            "patient_count": patient_count
        }
    
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }

@app.post("/api/debug/create-admin")
async def debug_create_admin():
    """Debug endpoint to manually create admin user"""
    import psycopg2
    import psycopg2.extras
    from passlib.context import CryptContext
    import uuid
    from datetime import datetime
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        return {"error": "DATABASE_URL not configured"}
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
        if cursor.fetchone():
            conn.close()
            return {"message": "Admin user already exists"}
        
        # Create admin user
        admin_id = str(uuid.uuid4())
        admin_password = pwd_context.hash("password")
        admin_email = "admin@jajuwa.com"
        admin_name = "Administrator"
        now = datetime.utcnow()
        
        cursor.execute("""
            INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (admin_id, "admin", admin_email, admin_name, admin_password, "admin", now, True))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Admin user created successfully",
            "username": "admin",
            "password": "password",
            "id": admin_id
        }
    
    except Exception as e:
        return {
            "error": f"Failed to create admin user: {str(e)}"
        }


# Load ONLY the full backend - no fallback
logger.info("Forcing full backend load...")

# Mock any problematic dependencies upfront
try:
    import aiofiles
except ImportError:
    logger.info("aiofiles not available, creating mock")
    class MockAioFiles:
        @staticmethod
        async def open(*args, **kwargs):
            raise Exception("aiofiles not available")
    sys.modules['aiofiles'] = MockAioFiles()

# Import the full backend directly
try:
    logger.info("Importing server_postgresql_fully_optimized directly...")
    
    # Import with mocking in place
    import server_postgresql_fully_optimized as backend
    
    # Patch the lifespan if it exists
    if hasattr(backend, 'lifespan'):
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def mock_lifespan(app):
            logger.info("Serverless mode: skipping lifespan events")
            yield
        
        backend.lifespan = mock_lifespan
        logger.info("Patched lifespan function for serverless")
    
    # Include the router
    if hasattr(backend, 'api_router'):
        app.include_router(backend.api_router)
        logger.info("Successfully included full backend api_router")
        full_backend_success = True
    else:
        logger.error("api_router not found in backend module")
        raise ImportError("api_router not found")
        
except Exception as e:
    logger.error(f"CRITICAL: Failed to load full backend: {e}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # Don't fallback - force the error to be visible
    @app.get("/api/auth/login")
    async def backend_error():
        return {"error": "Backend failed to load", "details": str(e)}
    
    full_backend_success = False

logger.info("PAC System API initialized successfully")
