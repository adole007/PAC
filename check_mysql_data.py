#!/usr/bin/env python3
"""
Check what data exists in MySQL database before migration
"""

import mysql.connector
from getpass import getpass

# MySQL configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'pac_user',
    'password': 'pac_password',
    'database': 'jajuwa_pac_system',
    'port': 3306
}

def check_mysql_data():
    """Check what data exists in MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("🔍 Checking MySQL database contents...")
        print("=" * 50)
        
        # Check each table
        tables = ['users', 'patients', 'medical_images', 'audit_logs']
        
        total_records = 0
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                count = result['count'] if result else 0
                total_records += count
                
                print(f"\n📊 {table}: {count} records")
                
                if count > 0:
                    # Show sample data
                    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                    samples = cursor.fetchall()
                    
                    print(f"   Sample data:")
                    for i, sample in enumerate(samples, 1):
                        # Show only key fields to avoid clutter
                        key_fields = {}
                        for key, value in sample.items():
                            if key in ['id', 'username', 'email', 'patient_id', 'first_name', 'last_name', 'study_id', 'action']:
                                key_fields[key] = str(value)[:50] + '...' if len(str(value)) > 50 else value
                        print(f"   {i}. {key_fields}")
                        
            except mysql.connector.Error as e:
                print(f"❌ Error checking {table}: {e}")
        
        cursor.close()
        conn.close()
        
        print(f"\n{'=' * 50}")
        print(f"✅ MySQL database check completed")
        print(f"📊 Total records to migrate: {total_records}")
        
        if total_records == 0:
            print("⚠️  No data found in MySQL database!")
            print("Make sure your MySQL database has been set up and populated.")
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection error: {e}")
        
        # Try with password prompt
        try:
            password = getpass("Enter MySQL password: ")
            config = MYSQL_CONFIG.copy()
            config['password'] = password
            
            conn = mysql.connector.connect(**config)
            print("✅ Connected with provided password")
            # Repeat the check with new connection
            check_mysql_data_with_conn(conn)
            
        except mysql.connector.Error as e2:
            print(f"❌ Still failed: {e2}")
            print("Please check if MySQL is running and the PAC database exists.")

def check_mysql_data_with_conn(conn):
    """Check MySQL data with existing connection"""
    cursor = conn.cursor(dictionary=True)
    
    print("🔍 Checking MySQL database contents...")
    print("=" * 50)
    
    tables = ['users', 'patients', 'medical_images', 'audit_logs']
    total_records = 0
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            total_records += count
            
            print(f"\n📊 {table}: {count} records")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                samples = cursor.fetchall()
                
                print(f"   Sample data:")
                for i, sample in enumerate(samples, 1):
                    # Show only key fields to avoid clutter
                    key_fields = {}
                    for key, value in sample.items():
                        if key in ['id', 'username', 'email', 'patient_id', 'first_name', 'last_name', 'study_id', 'action']:
                            key_fields[key] = str(value)[:50] + '...' if len(str(value)) > 50 else value
                    print(f"   {i}. {key_fields}")
                    
        except mysql.connector.Error as e:
            print(f"❌ Error checking {table}: {e}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'=' * 50}")
    print(f"✅ MySQL database check completed")
    print(f"📊 Total records to migrate: {total_records}")

if __name__ == "__main__":
    check_mysql_data()
