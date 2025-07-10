#!/usr/bin/env python3
"""
Update user passwords in Supabase with proper hashing
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

def update_user_passwords():
    """Update user passwords with proper hashing"""
    print("Updating user passwords...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Define the correct passwords
        users_to_update = [
            {'username': 'admin', 'password': 'admin123'},
            {'username': 'clinician', 'password': 'admin123'}
        ]
        
        for user_info in users_to_update:
            username = user_info['username']
            password = user_info['password']
            
            # Create new password hash
            new_hash = pwd_context.hash(password)
            
            # Update the user's password
            cursor.execute(
                "UPDATE users SET hashed_password = %s WHERE username = %s",
                (new_hash, username)
            )
            
            print(f"✅ Updated password for {username}")
            
        conn.commit()
        
        # Verify the updates
        print("\nVerifying updated passwords:")
        cursor.execute("SELECT username, hashed_password FROM users")
        users = cursor.fetchall()
        
        for user in users:
            username = user['username']
            stored_hash = user['hashed_password']
            
            # Test with the expected password
            test_password = 'admin123'
            
            try:
                if pwd_context.verify(test_password, stored_hash):
                    print(f"✅ {username} password verification successful")
                else:
                    print(f"❌ {username} password verification failed")
            except Exception as e:
                print(f"❌ Error verifying {username}: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = update_user_passwords()
    if success:
        print("\n🎉 Password update completed!")
        print("You can now login with:")
        print("  Username: admin, Password: admin123")
        print("  Username: clinician, Password: admin123")
    else:
        print("\n❌ Password update failed!")
