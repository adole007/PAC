#!/usr/bin/env python3
"""
Test login credentials in Supabase
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_user_credentials():
    """Test user credentials from Supabase"""
    print("Testing user credentials...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all users
        cursor.execute("SELECT id, username, email, full_name, hashed_password, role, is_active FROM users;")
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - Username: {user['username']}")
            print(f"    Email: {user['email']}")
            print(f"    Full Name: {user['full_name']}")
            print(f"    Role: {user['role']}")
            print(f"    Active: {user['is_active']}")
            print(f"    Password Hash: {user['hashed_password'][:50]}...")
            print()
        
        # Test password verification
        print("Testing password verification:")
        for user in users:
            username = user['username']
            stored_hash = user['hashed_password']
            
            # Test with common passwords
            test_passwords = ['admin123', 'password', 'admin', 'clinician', 'test123']
            
            for test_pwd in test_passwords:
                try:
                    if pwd_context.verify(test_pwd, stored_hash):
                        print(f"✅ {username} password is: {test_pwd}")
                        break
                except Exception as e:
                    print(f"❌ Error verifying {test_pwd} for {username}: {e}")
            else:
                print(f"❌ Could not verify password for {username}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_user_credentials()
