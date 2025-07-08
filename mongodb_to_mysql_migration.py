#!/usr/bin/env python3
"""
MongoDB to MySQL Migration Script for JAJUWA HEALTHCARE PAC System
"""

import pymongo
import mysql.connector
import json
import uuid
from datetime import datetime
import sys

# MongoDB connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["test_database"]

# MySQL connection
mysql_conn = mysql.connector.connect(
    host='localhost',
    user='pac_user',
    password='pac_password',
    database='jajuwa_pac_system'
)
mysql_cursor = mysql_conn.cursor()

def migrate_users():
    """Migrate users from MongoDB to MySQL"""
    print("Migrating users...")
    
    # Clear existing users (except pre-inserted ones)
    mysql_cursor.execute("DELETE FROM users WHERE username NOT IN ('admin', 'clinician')")
    
    users = list(mongo_db.users.find())
    for user in users:
        # Skip if user already exists
        mysql_cursor.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
        if mysql_cursor.fetchone():
            print(f"User {user['username']} already exists, updating...")
            mysql_cursor.execute("""
                UPDATE users SET 
                email = %s, full_name = %s, hashed_password = %s, 
                role = %s, is_active = %s, last_login = %s
                WHERE username = %s
            """, (
                user['email'], user['full_name'], user.get('hashed_password', ''),
                user['role'], user.get('is_active', True), 
                user.get('last_login'), user['username']
            ))
        else:
            mysql_cursor.execute("""
                INSERT INTO users (id, username, email, full_name, hashed_password, role, is_active, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user['id'], user['username'], user['email'], user['full_name'],
                user.get('hashed_password', ''), user['role'], user.get('is_active', True),
                user.get('created_at'), user.get('last_login')
            ))
    
    mysql_conn.commit()
    print(f"Migrated {len(users)} users")

def migrate_patients():
    """Migrate patients from MongoDB to MySQL"""
    print("Migrating patients...")
    
    mysql_cursor.execute("DELETE FROM patients")
    
    patients = list(mongo_db.patients.find())
    for patient in patients:
        mysql_cursor.execute("""
            INSERT INTO patients (
                id, patient_id, first_name, last_name, date_of_birth, gender,
                phone, email, address, medical_record_number, primary_physician,
                allergies, medications, medical_history, insurance_provider,
                insurance_policy_number, insurance_group_number, consent_given,
                created_at, updated_at, created_by, last_accessed, access_log
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            patient['id'], patient['patient_id'], patient['first_name'], patient['last_name'],
            patient['date_of_birth'], patient['gender'], patient['phone'], 
            patient.get('email'), patient['address'], patient['medical_record_number'],
            patient['primary_physician'], json.dumps(patient.get('allergies', [])),
            json.dumps(patient.get('medications', [])), json.dumps(patient.get('medical_history', [])),
            patient['insurance_provider'], patient['insurance_policy_number'],
            patient.get('insurance_group_number'), patient.get('consent_given', False),
            patient.get('created_at'), patient.get('updated_at'), patient['created_by'],
            patient.get('last_accessed'), json.dumps(patient.get('access_log', []))
        ))
    
    mysql_conn.commit()
    print(f"Migrated {len(patients)} patients")

def migrate_medical_images():
    """Migrate medical images from MongoDB to MySQL"""
    print("Migrating medical images...")
    
    mysql_cursor.execute("DELETE FROM medical_images")
    
    images = list(mongo_db.medical_images.find())
    for image in images:
        mysql_cursor.execute("""
            INSERT INTO medical_images (
                id, patient_id, study_id, series_id, instance_id, modality,
                body_part, study_date, study_time, institution_name, referring_physician,
                dicom_metadata, image_data, thumbnail_data, original_filename,
                file_size, image_format, window_center, window_width,
                uploaded_at, uploaded_by, access_log
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            image['id'], image['patient_id'], image['study_id'], image['series_id'],
            image['instance_id'], image['modality'], image['body_part'],
            image['study_date'], image['study_time'], image['institution_name'],
            image['referring_physician'], json.dumps(image.get('dicom_metadata', {})),
            image['image_data'], image['thumbnail_data'], image['original_filename'],
            image['file_size'], image['image_format'], image.get('window_center'),
            image.get('window_width'), image.get('uploaded_at'), image['uploaded_by'],
            json.dumps(image.get('access_log', []))
        ))
    
    mysql_conn.commit()
    print(f"Migrated {len(images)} medical images")

def migrate_audit_logs():
    """Migrate audit logs from MongoDB to MySQL"""
    print("Migrating audit logs...")
    
    mysql_cursor.execute("DELETE FROM audit_logs")
    
    logs = list(mongo_db.audit_logs.find())
    for log in logs:
        mysql_cursor.execute("""
            INSERT INTO audit_logs (
                id, user_id, action, resource_type, resource_id,
                timestamp, ip_address, user_agent, details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            log['id'], log['user_id'], log['action'], log['resource_type'],
            log.get('resource_id'), log.get('timestamp'), log['ip_address'],
            log.get('user_agent'), json.dumps(log.get('details', {}))
        ))
    
    mysql_conn.commit()
    print(f"Migrated {len(logs)} audit logs")

def verify_migration():
    """Verify the migration was successful"""
    print("\nVerifying migration...")
    
    # Check counts
    tables = ['users', 'patients', 'medical_images', 'audit_logs']
    for table in tables:
        mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        mysql_count = mysql_cursor.fetchone()[0]
        
        if table == 'users':
            mongo_count = mongo_db.users.count_documents({})
        elif table == 'patients':
            mongo_count = mongo_db.patients.count_documents({})
        elif table == 'medical_images':
            mongo_count = mongo_db.medical_images.count_documents({})
        elif table == 'audit_logs':
            mongo_count = mongo_db.audit_logs.count_documents({})
        
        print(f"{table}: MongoDB={mongo_count}, MySQL={mysql_count}")
        if mysql_count >= mongo_count:
            print(f"✅ {table} migration successful")
        else:
            print(f"❌ {table} migration incomplete")

if __name__ == "__main__":
    try:
        print("Starting MongoDB to MySQL migration for JAJUWA HEALTHCARE PAC System...")
        print("=" * 60)
        
        migrate_users()
        migrate_patients()
        migrate_medical_images()
        migrate_audit_logs()
        
        verify_migration()
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        mysql_conn.rollback()
        sys.exit(1)
    finally:
        mysql_cursor.close()
        mysql_conn.close()
        mongo_client.close()