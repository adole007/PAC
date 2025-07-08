#!/usr/bin/env python3
"""
Simple MySQL Setup for PAC System
This script will create the database and tables needed
"""

import mysql.connector
import sys
import os
from pathlib import Path

def setup_mysql_database():
    """Setup MySQL database with root user"""
    try:
        # Connect with root user (no password assumed for local development)
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''  # Change this if your MySQL root has a password
        )
        cursor = conn.cursor()
        
        # Create database
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS jajuwa_pac_system")
        cursor.execute("USE jajuwa_pac_system")
        
        # Create user and grant privileges
        print("Creating user...")
        try:
            cursor.execute("DROP USER IF EXISTS 'pac_user'@'localhost'")
            cursor.execute("CREATE USER 'pac_user'@'localhost' IDENTIFIED BY 'pac_password'")
            cursor.execute("GRANT ALL PRIVILEGES ON jajuwa_pac_system.* TO 'pac_user'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
        except mysql.connector.Error as e:
            print(f"User creation warning: {e}")
        
        # Read and execute schema
        print("Creating tables...")
        schema_file = Path(__file__).parent / "create_mysql_schema.sql"
        with open(schema_file, 'r') as f:
            schema_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    print(f"Warning executing statement: {e}")
        
        conn.commit()
        print("✅ Database setup completed successfully!")
        
        # Test connection with new user
        print("Testing new user connection...")
        test_conn = mysql.connector.connect(
            host='localhost',
            user='pac_user',
            password='pac_password',
            database='jajuwa_pac_system'
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT COUNT(*) FROM users")
        user_count = test_cursor.fetchone()[0]
        print(f"✅ Connection test successful! Found {user_count} users in database.")
        
        test_cursor.close()
        test_conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_env_file():
    """Create MySQL environment file"""
    env_content = """# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=pac_user
MYSQL_PASSWORD=pac_password
MYSQL_DATABASE=jajuwa_pac_system
MYSQL_PORT=3306

# Keep existing settings
SECRET_KEY=your-secret-key-change-this-in-production
"""
    
    with open("backend/.env.mysql", "w") as f:
        f.write(env_content)
    
    print("✅ Created backend/.env.mysql file")

if __name__ == "__main__":
    print("Setting up MySQL for PAC System...")
    print("=" * 50)
    
    if setup_mysql_database():
        create_env_file()
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Make sure MySQL is running")
        print("2. Use the credentials:")
        print("   - Database: jajuwa_pac_system")
        print("   - User: pac_user")
        print("   - Password: pac_password")
        print("3. Update your backend to use MySQL")
    else:
        print("\n❌ Setup failed. Make sure MySQL is running and accessible.")
        sys.exit(1)
