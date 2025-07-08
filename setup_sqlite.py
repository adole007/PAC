#!/usr/bin/env python3
"""
SQLite Setup for PAC System (MySQL Alternative)
This creates a local SQLite database that works immediately without MySQL installation
"""

import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
import hashlib

def create_sqlite_database():
    """Create SQLite database with all tables"""
    db_path = Path(__file__).parent / "pac_system.db"
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('clinician', 'admin')),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        )
    """)
    
    # Create patients table
    cursor.execute("""
        CREATE TABLE patients (
            id VARCHAR(36) PRIMARY KEY,
            patient_id VARCHAR(50) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            date_of_birth DATE NOT NULL,
            gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(100),
            address TEXT NOT NULL,
            medical_record_number VARCHAR(50) UNIQUE NOT NULL,
            primary_physician VARCHAR(100) NOT NULL,
            allergies TEXT, -- JSON as text
            medications TEXT, -- JSON as text
            medical_history TEXT, -- JSON as text
            insurance_provider VARCHAR(100) NOT NULL,
            insurance_policy_number VARCHAR(100) NOT NULL,
            insurance_group_number VARCHAR(100),
            consent_given BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) NOT NULL,
            last_accessed TIMESTAMP NULL,
            access_log TEXT, -- JSON as text
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    
    # Create medical_images table
    cursor.execute("""
        CREATE TABLE medical_images (
            id VARCHAR(36) PRIMARY KEY,
            patient_id VARCHAR(36) NOT NULL,
            study_id VARCHAR(100) NOT NULL,
            series_id VARCHAR(100) NOT NULL,
            instance_id VARCHAR(36) NOT NULL,
            modality VARCHAR(50) NOT NULL,
            body_part VARCHAR(100) NOT NULL,
            study_date DATE NOT NULL,
            study_time TIME NOT NULL,
            institution_name VARCHAR(200) NOT NULL,
            referring_physician VARCHAR(100) NOT NULL,
            dicom_metadata TEXT, -- JSON as text
            image_data TEXT NOT NULL, -- Base64 image data
            thumbnail_data TEXT NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_size INTEGER NOT NULL,
            image_format VARCHAR(50) NOT NULL,
            window_center REAL,
            window_width REAL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by VARCHAR(36) NOT NULL,
            access_log TEXT, -- JSON as text
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)
    
    # Create audit_logs table
    cursor.execute("""
        CREATE TABLE audit_logs (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'UPLOAD', 'LOGIN', 'LOGOUT')),
            resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('user', 'patient', 'medical_image', 'system')),
            resource_id VARCHAR(36),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45) NOT NULL,
            user_agent TEXT,
            details TEXT, -- JSON as text
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_username ON users(username)")
    cursor.execute("CREATE INDEX idx_patient_id ON patients(patient_id)")
    cursor.execute("CREATE INDEX idx_mrn ON patients(medical_record_number)")
    cursor.execute("CREATE INDEX idx_images_patient ON medical_images(patient_id)")
    cursor.execute("CREATE INDEX idx_audit_user ON audit_logs(user_id)")
    
    # Insert default users with bcrypt password hash for 'admin123'
    admin_id = str(uuid.uuid4())
    clinician_id = str(uuid.uuid4())
    
    # Hash for 'admin123' using bcrypt
    admin_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj.A7J/7O2yW"
    
    cursor.execute("""
        INSERT INTO users (id, username, email, full_name, hashed_password, role, created_at) VALUES
        (?, 'admin', 'admin@hospital.com', 'Administrator', ?, 'admin', ?),
        (?, 'clinician', 'doctor@hospital.com', 'Dr. Smith', ?, 'clinician', ?)
    """, (admin_id, admin_hash, datetime.now().isoformat(),
          clinician_id, admin_hash, datetime.now().isoformat()))
    
    conn.commit()
    
    # Test the database
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ SQLite database created: {db_path}")
    print(f"✅ Created {user_count} users")
    print("✅ Default login credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    
    return str(db_path)

def create_sqlite_env():
    """Create environment file for SQLite"""
    env_content = """# SQLite Database Configuration
DATABASE_URL=sqlite:///pac_system.db
DB_TYPE=sqlite

# Keep existing settings
SECRET_KEY=your-secret-key-change-this-in-production
"""
    
    with open("backend/.env.sqlite", "w") as f:
        f.write(env_content)
    
    print("✅ Created backend/.env.sqlite file")

if __name__ == "__main__":
    print("Setting up SQLite for PAC System...")
    print("=" * 50)
    
    try:
        db_path = create_sqlite_database()
        create_sqlite_env()
        
        print("\n" + "=" * 50)
        print("SQLite setup completed successfully!")
        print(f"\nDatabase file: {db_path}")
        print("\nDefault credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nNext: Update backend to use SQLite")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
