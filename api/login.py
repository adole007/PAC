# Login serverless function for Vercel
from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
import psycopg2.extras
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'jajuwa_pac_system')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.environ.get('DATABASE_URL')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify password with fallback for different hash formats"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback: check if it's a simple hash (for development)
        if hashed_password == plain_password:
            return True
        return False

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
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            data = json.loads(post_data.decode())
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                self.send_error_response(400, "Username and password are required")
                return
            
            # Connect to database
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Find user
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            
            if not user_row:
                conn.close()
                self.send_error_response(401, "Incorrect username or password")
                return
            
            user_dict = dict(user_row)
            
            # Verify password
            if not verify_password(password, user_dict["hashed_password"]):
                conn.close()
                self.send_error_response(401, "Incorrect username or password")
                return
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = %s WHERE username = %s", 
                          (datetime.utcnow(), username))
            conn.commit()
            conn.close()
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_dict["username"]}, expires_delta=access_token_expires
            )
            
            # Remove password from response
            user_dict.pop('hashed_password', None)
            
            # Convert datetime objects to strings
            for key, value in user_dict.items():
                if isinstance(value, datetime):
                    user_dict[key] = value.isoformat()
            
            response = {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_dict
            }
            
            self.send_success_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        error_response = {"detail": message}
        self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
