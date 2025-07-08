#!/usr/bin/env python3
"""
Complete MySQL Setup and Data Migration for PAC System
This script will:
1. Create MySQL database and user
2. Create tables from schema
3. Migrate data from SQLite to MySQL
4. Test the connection
"""

import mysql.connector
import sqlite3
import json
import sys
import os
from pathlib import Path
from getpass import getpass

def get_mysql_root_connection():
    """Get MySQL root connection with password prompt"""
    print("Connecting to MySQL as root user...")
    
    # Try connecting without password first
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        print("✅ Connected to MySQL without password")
        return conn
    except mysql.connector.Error:
        pass
    
    # Prompt for password
    for attempt in range(3):
        try:
            password = getpass("Enter MySQL root password (or press Enter if none): ").strip()
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=password if password else ''
            )
            print("✅ Connected to MySQL with password")
            return conn
        except mysql.connector.Error as e:
            print(f"❌ Failed to connect: {e}")
            if attempt < 2:
                print("Please try again...")
    
    raise Exception("Could not connect to MySQL after 3 attempts")

def create_mysql_database_and_user(root_conn):
    """Create database and user"""
    cursor = root_conn.cursor()
    
    try:
        # Create database
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS jajuwa_pac_system")
        cursor.execute("USE jajuwa_pac_system")
        
        # Create user and grant privileges
        print("Creating user and setting permissions...")
        cursor.execute("DROP USER IF EXISTS 'pac_user'@'localhost'")
        cursor.execute("CREATE USER 'pac_user'@'localhost' IDENTIFIED BY 'pac_password'")
        cursor.execute("GRANT ALL PRIVILEGES ON jajuwa_pac_system.* TO 'pac_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        root_conn.commit()
        print("✅ Database and user created successfully")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating database/user: {e}")
        return False

def create_mysql_tables(root_conn):
    """Create tables using the schema file"""
    cursor = root_conn.cursor()
    
    try:
        cursor.execute("USE jajuwa_pac_system")
        
        # Read schema file
        schema_file = Path(__file__).parent / "create_mysql_schema.sql"
        with open(schema_file, 'r') as f:
            schema_content = f.read()
        
        # Execute schema statements
        print("Creating tables...")
        statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    if "already exists" not in str(e) and "Duplicate entry" not in str(e):
                        print(f"Warning: {e}")
        
        root_conn.commit()
        print("✅ Tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def migrate_data_from_sqlite():
    """Migrate data from SQLite to MySQL"""
    sqlite_db = Path(__file__).parent / "pac_system.db"
    
    if not sqlite_db.exists():
        print("⚠️  No SQLite database found - creating default admin user in MySQL")
        return create_default_users()
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(str(sqlite_db))
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to MySQL
        mysql_conn = mysql.connector.connect(
            host='localhost',
            user='pac_user',
            password='pac_password',
            database='jajuwa_pac_system'
        )
        mysql_cursor = mysql_conn.cursor()
        
        print("Migrating data from SQLite to MySQL...")
        
        # Migrate users
        print("  - Migrating users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            mysql_cursor.execute("""
                INSERT IGNORE INTO users (id, username, email, full_name, hashed_password, role, is_active, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user['id'], user['username'], user['email'], user['full_name'],
                user['hashed_password'], user['role'], user['is_active'],
                user['created_at'], user['last_login']
            ))
        
        # Migrate patients (if any)
        print("  - Migrating patients...")
        sqlite_cursor.execute("SELECT * FROM patients")
        patients = sqlite_cursor.fetchall()
        
        for patient in patients:
            mysql_cursor.execute("""
                INSERT IGNORE INTO patients (
                    id, patient_id, first_name, last_name, date_of_birth, gender,
                    phone, email, address, medical_record_number, primary_physician,
                    allergies, medications, medical_history, insurance_provider,
                    insurance_policy_number, insurance_group_number, consent_given,
                    created_at, updated_at, created_by, last_accessed, access_log
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient['id'], patient['patient_id'], patient['first_name'], patient['last_name'],
                patient['date_of_birth'], patient['gender'], patient['phone'], patient['email'],
                patient['address'], patient['medical_record_number'], patient['primary_physician'],
                patient['allergies'], patient['medications'], patient['medical_history'],
                patient['insurance_provider'], patient['insurance_policy_number'],
                patient['insurance_group_number'], patient['consent_given'],
                patient['created_at'], patient['updated_at'], patient['created_by'],
                patient['last_accessed'], patient['access_log']
            ))
        
        mysql_conn.commit()
        
        # Check migration results
        mysql_cursor.execute("SELECT COUNT(*) FROM users")
        user_count = mysql_cursor.fetchone()[0]
        
        mysql_cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = mysql_cursor.fetchone()[0]
        
        print(f"✅ Migration completed: {user_count} users, {patient_count} patients")
        
        sqlite_conn.close()
        mysql_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def create_default_users():
    """Create default admin user if no SQLite data exists"""
    try:
        mysql_conn = mysql.connector.connect(
            host='localhost',
            user='pac_user',
            password='pac_password',
            database='jajuwa_pac_system'
        )
        cursor = mysql_conn.cursor()
        
        # Create admin user with known password hash
        admin_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.A7J/7O2yW"
        
        cursor.execute("""
            INSERT IGNORE INTO users (id, username, email, full_name, hashed_password, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            'admin-001', 'admin', 'admin@hospital.com', 'Administrator', admin_hash, 'admin'
        ))
        
        cursor.execute("""
            INSERT IGNORE INTO users (id, username, email, full_name, hashed_password, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            'clinician-001', 'clinician', 'doctor@hospital.com', 'Dr. Smith', admin_hash, 'clinician'
        ))
        
        mysql_conn.commit()
        mysql_conn.close()
        
        print("✅ Default users created")
        return True
        
    except Exception as e:
        print(f"❌ Error creating default users: {e}")
        return False

def test_mysql_connection():
    """Test the MySQL connection and user authentication"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='pac_user',
            password='pac_password',
            database='jajuwa_pac_system'
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        
        print("✅ MySQL connection test successful")
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user[0]} ({user[1]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def create_mysql_env_file():
    """Create MySQL environment file for the backend"""
    env_content = """# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=pac_user
MYSQL_PASSWORD=pac_password
MYSQL_DATABASE=jajuwa_pac_system
MYSQL_PORT=3306

# Backend Configuration
SECRET_KEY=your-secret-key-change-this-in-production
"""
    
    with open("backend/.env.mysql", "w") as f:
        f.write(env_content)
    
    print("✅ Created backend/.env.mysql file")

if __name__ == "__main__":
    print("Setting up MySQL for PAC System...")
    print("=" * 60)
    
    try:
        # Step 1: Connect as root
        root_conn = get_mysql_root_connection()
        
        # Step 2: Create database and user
        if not create_mysql_database_and_user(root_conn):
            sys.exit(1)
        
        # Step 3: Create tables
        if not create_mysql_tables(root_conn):
            sys.exit(1)
        
        root_conn.close()
        
        # Step 4: Migrate data
        if not migrate_data_from_sqlite():
            sys.exit(1)
        
        # Step 5: Test connection
        if not test_mysql_connection():
            sys.exit(1)
        
        # Step 6: Create environment file
        create_mysql_env_file()
        
        print("\n" + "=" * 60)
        print("✅ MySQL setup completed successfully!")
        print("\nDatabase Details:")
        print("  Host: localhost")
        print("  Database: jajuwa_pac_system")
        print("  User: pac_user")
        print("  Password: pac_password")
        print("\nDefault Login Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nNext steps:")
        print("1. Update backend to use MySQL")
        print("2. Start the backend server")
        print("3. Test login in frontend")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
