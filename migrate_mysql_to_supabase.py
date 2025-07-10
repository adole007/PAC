#!/usr/bin/env python3
"""
MySQL to Supabase (PostgreSQL) Data Migration Script
This script will:
1. Connect to your local MySQL database
2. Export all data from MySQL tables
3. Transform the data for PostgreSQL compatibility
4. Import the data into your Supabase database
"""

import mysql.connector
import psycopg2
import psycopg2.extras
import json
import uuid
import sys
import os
from datetime import datetime
from getpass import getpass
from pathlib import Path

# Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'pac_user',
    'password': 'pac_password',
    'database': 'jajuwa_pac_system',
    'port': 3306
}

# You need to fill these with your Supabase connection details
SUPABASE_CONFIG = {
    'host': 'db.fjmlshmkdaufqkefmixw.supabase.co',
    'user': 'postgres',
    'password': 'jajuwa@pac@',  # Your Supabase password
    'database': 'postgres',
    'port': 5432
}

def get_mysql_connection():
    """Get MySQL connection"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✅ Connected to MySQL database")
        return conn
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection error: {e}")
        
        # Try prompting for password
        try:
            password = getpass("Enter MySQL password: ")
            config = MYSQL_CONFIG.copy()
            config['password'] = password
            conn = mysql.connector.connect(**config)
            print("✅ Connected to MySQL database with provided password")
            return conn
        except mysql.connector.Error as e2:
            print(f"❌ MySQL connection failed: {e2}")
            return None

def get_supabase_connection():
    """Get Supabase PostgreSQL connection"""
    if not SUPABASE_CONFIG['host'] or not SUPABASE_CONFIG['password']:
        print("❌ Please configure your Supabase connection details in the script")
        print("Update SUPABASE_CONFIG with your Supabase database credentials")
        return None
    
    try:
        conn = psycopg2.connect(
            host=SUPABASE_CONFIG['host'],
            user=SUPABASE_CONFIG['user'],
            password=SUPABASE_CONFIG['password'],
            database=SUPABASE_CONFIG['database'],
            port=SUPABASE_CONFIG['port']
        )
        print("✅ Connected to Supabase database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Supabase connection error: {e}")
        return None

def convert_mysql_to_postgres_data(table_name, mysql_data):
    """Convert MySQL data format to PostgreSQL format"""
    converted_data = []
    
    for row in mysql_data:
        converted_row = {}
        
        for key, value in row.items():
            if value is None:
                converted_row[key] = None
            elif isinstance(value, str) and key == 'id':
                # Convert string UUIDs to proper UUID format
                try:
                    converted_row[key] = str(uuid.UUID(value))
                except ValueError:
                    # If not a valid UUID, generate a new one
                    converted_row[key] = str(uuid.uuid4())
            elif key in ['allergies', 'medications', 'medical_history', 'dicom_metadata', 'access_log', 'details']:
                # Handle JSON fields
                if isinstance(value, str):
                    try:
                        converted_row[key] = json.loads(value)
                    except json.JSONDecodeError:
                        converted_row[key] = [] if key in ['allergies', 'medications', 'medical_history', 'access_log'] else {}
                else:
                    converted_row[key] = value
            elif isinstance(value, datetime):
                # PostgreSQL timestamp format
                converted_row[key] = value
            else:
                converted_row[key] = value
        
        converted_data.append(converted_row)
    
    return converted_data

def export_mysql_table(mysql_conn, table_name):
    """Export data from MySQL table"""
    try:
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        cursor.close()
        
        print(f"✅ Exported {len(data)} rows from {table_name}")
        return data
    except mysql.connector.Error as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return []

def import_to_supabase_table(supabase_conn, table_name, data):
    """Import data to Supabase table"""
    if not data:
        print(f"⚠️  No data to import for {table_name}")
        return True
    
    try:
        cursor = supabase_conn.cursor()
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        # Create INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        insert_query = f"""
            INSERT INTO {table_name} ({columns_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT (id) DO NOTHING
        """
        
        # Prepare data for insertion
        values_list = []
        for row in data:
            values = []
            for col in columns:
                value = row[col]
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
            values_list.append(values)
        
        # Execute batch insert
        cursor.executemany(insert_query, values_list)
        supabase_conn.commit()
        cursor.close()
        
        print(f"✅ Imported {len(data)} rows to {table_name}")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error importing to {table_name}: {e}")
        supabase_conn.rollback()
        return False

def migrate_table(mysql_conn, supabase_conn, table_name):
    """Migrate a single table from MySQL to Supabase"""
    print(f"\n🔄 Migrating {table_name}...")
    
    # Export from MySQL
    mysql_data = export_mysql_table(mysql_conn, table_name)
    if not mysql_data:
        return True
    
    # Convert data format
    converted_data = convert_mysql_to_postgres_data(table_name, mysql_data)
    
    # Import to Supabase
    return import_to_supabase_table(supabase_conn, table_name, converted_data)

def check_table_exists(conn, table_name, is_postgres=False):
    """Check if table exists in database"""
    try:
        cursor = conn.cursor()
        if is_postgres:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
        else:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        
        result = cursor.fetchone()
        cursor.close()
        
        if is_postgres:
            return result[0] if result else False
        else:
            return bool(result)
            
    except Exception as e:
        print(f"❌ Error checking table {table_name}: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting MySQL to Supabase Migration")
    print("=" * 50)
    
    # Check if Supabase config is set
    if not SUPABASE_CONFIG['password']:
        print("📋 Please provide your Supabase database password:")
        print("(Find this in your Supabase dashboard under Settings → Database)")
        SUPABASE_CONFIG['password'] = getpass("Supabase Database Password: ").strip()
        
        if not SUPABASE_CONFIG['password']:
            print("❌ Database password is required!")
            return False
    
    # Connect to databases
    mysql_conn = get_mysql_connection()
    if not mysql_conn:
        return False
    
    supabase_conn = get_supabase_connection()
    if not supabase_conn:
        mysql_conn.close()
        return False
    
    # Tables to migrate (in order due to foreign key constraints)
    tables_to_migrate = ['users', 'patients', 'medical_images', 'audit_logs']
    
    success = True
    
    for table_name in tables_to_migrate:
        # Check if table exists in both databases
        if not check_table_exists(mysql_conn, table_name, is_postgres=False):
            print(f"⚠️  Table {table_name} not found in MySQL - skipping")
            continue
            
        if not check_table_exists(supabase_conn, table_name, is_postgres=True):
            print(f"❌ Table {table_name} not found in Supabase - make sure schema is created")
            success = False
            continue
        
        # Migrate the table
        if not migrate_table(mysql_conn, supabase_conn, table_name):
            success = False
    
    # Close connections
    mysql_conn.close()
    supabase_conn.close()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your backend code to use PostgreSQL")
        print("2. Update environment variables with Supabase credentials")
        print("3. Test your application")
    else:
        print("\n❌ Migration completed with errors")
        print("Please check the error messages above and fix any issues")
    
    return success

if __name__ == "__main__":
    print("MySQL to Supabase Migration Tool")
    print("=" * 40)
    
    # Prompt for Supabase credentials if not set
    if not SUPABASE_CONFIG['host']:
        print("\n📋 Please provide your Supabase connection details:")
        SUPABASE_CONFIG['host'] = input("Supabase Host (e.g., db.xxx.supabase.co): ").strip()
        SUPABASE_CONFIG['password'] = getpass("Supabase Password: ").strip()
        
        if not SUPABASE_CONFIG['host'] or not SUPABASE_CONFIG['password']:
            print("❌ Host and password are required!")
            sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
