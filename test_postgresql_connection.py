#!/usr/bin/env python3
"""
Test PostgreSQL connection to Supabase
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

def test_postgresql_connection():
    """Test PostgreSQL connection and query users"""
    print("Testing PostgreSQL connection...")
    print(f"Database URL: {DATABASE_URL}")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        # Test users table
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users count: {user_count}")
        
        # Test specific users
        cursor.execute("SELECT username, role FROM users LIMIT 5;")
        users = cursor.fetchall()
        print(f"✅ Users found:")
        for user in users:
            print(f"   - {user['username']} ({user['role']})")
        
        conn.close()
        print("✅ PostgreSQL connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    if success:
        print("\n🎉 Ready to run backend server with PostgreSQL!")
    else:
        print("\n❌ Connection failed. Please check your DATABASE_URL.")
