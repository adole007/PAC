#!/usr/bin/env python3
"""
Test SQLite database and login functionality
"""

import sqlite3
import requests
import json
from pathlib import Path
from passlib.context import CryptContext

def test_database():
    """Test SQLite database directly"""
    db_path = Path(__file__).parent / "pac_system.db"
    
    if not db_path.exists():
        print("❌ Database file not found! Run setup_sqlite.py first.")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT username, email, role FROM users")
        users = cursor.fetchall()
        
        print("✅ Database connection successful")
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user[0]} ({user[1]}) - {user[2]}")
        
        # Check password hash
        cursor.execute("SELECT username, hashed_password FROM users WHERE username = 'admin'")
        admin_data = cursor.fetchone()
        
        if admin_data:
            print(f"✅ Admin user found")
            print(f"   Hash: {admin_data[1][:50]}...")
            
            # Test password verification
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            is_valid = pwd_context.verify("admin123", admin_data[1])
            print(f"   Password verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_backend_api():
    """Test backend API login"""
    backend_url = "http://localhost:8001"
    
    # Test health endpoint
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
            print(f"   Users: {health_data.get('users')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not reachable: {e}")
        print("   Make sure to run: python backend/server_sqlite.py")
        return False
    
    # Test login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print(f"   Token: {token_data['access_token'][:50]}...")
            print(f"   User: {token_data['user']['username']} - {token_data['user']['role']}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False

def fix_password_hash():
    """Fix password hash in database if needed"""
    db_path = Path(__file__).parent / "pac_system.db"
    
    if not db_path.exists():
        print("❌ Database not found")
        return False
    
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        new_hash = pwd_context.hash("admin123")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET hashed_password = ? WHERE username = 'admin'", (new_hash,))
        cursor.execute("UPDATE users SET hashed_password = ? WHERE username = 'clinician'", (new_hash,))
        
        conn.commit()
        conn.close()
        
        print("✅ Password hashes updated")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix passwords: {e}")
        return False

if __name__ == "__main__":
    print("Testing PAC SQLite Login System...")
    print("=" * 50)
    
    # Test database
    if not test_database():
        print("\n🔧 Attempting to fix password hashes...")
        if fix_password_hash():
            print("   Retesting database...")
            test_database()
    
    print("\n" + "=" * 50)
    print("Testing Backend API...")
    
    # Test backend
    test_backend_api()
    
    print("\n" + "=" * 50)
    print("If backend tests fail, start the server with:")
    print("python backend/server_sqlite.py")
    print("\nThen try logging in with:")
    print("Username: admin")
    print("Password: admin123")
