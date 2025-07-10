#!/usr/bin/env python3
"""
Export MySQL data to SQL files for manual import to Supabase
"""

import mysql.connector
import json
import uuid
import os
from datetime import datetime
from getpass import getpass

# MySQL configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'pac_user',
    'password': 'pac_password',
    'database': 'jajuwa_pac_system',
    'port': 3306
}

def convert_value_for_postgres(value, column_name):
    """Convert MySQL value to PostgreSQL format"""
    if value is None:
        return 'NULL'
    
    # Handle UUID fields
    if column_name == 'id' or column_name.endswith('_id'):
        if isinstance(value, str):
            try:
                # Validate UUID format
                uuid.UUID(value)
                return f"'{value}'"
            except ValueError:
                # Generate new UUID if invalid
                return f"'{str(uuid.uuid4())}'"
    
    # Handle JSON fields
    if column_name in ['allergies', 'medications', 'medical_history', 'dicom_metadata', 'access_log', 'details']:
        if isinstance(value, str):
            try:
                # Parse JSON to validate
                parsed = json.loads(value)
                return f"'{json.dumps(parsed)}'"
            except json.JSONDecodeError:
                # Default empty array/object
                default = '[]' if column_name in ['allergies', 'medications', 'medical_history', 'access_log'] else '{}'
                return f"'{default}'"
        else:
            return f"'{json.dumps(value)}'"
    
    # Handle datetime fields
    if isinstance(value, datetime):
        return f"'{value.isoformat()}'"
    
    # Handle string fields
    if isinstance(value, str):
        # Escape single quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    
    # Handle boolean fields
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    
    # Handle numeric fields
    if isinstance(value, (int, float)):
        return str(value)
    
    # Default: convert to string
    return f"'{str(value)}'"

def export_table_to_sql(mysql_conn, table_name, output_file):
    """Export MySQL table to PostgreSQL SQL file"""
    try:
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        cursor.close()
        
        if not data:
            print(f"⚠️  No data in {table_name}")
            return True
        
        print(f"📦 Exporting {len(data)} records from {table_name}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Data export for {table_name}\n")
            f.write(f"-- Generated on {datetime.now().isoformat()}\n\n")
            
            # Clear existing data
            f.write(f"DELETE FROM {table_name};\n\n")
            
            # Get column names from first row
            if data:
                columns = list(data[0].keys())
                
                # Write INSERT statements
                for row in data:
                    values = []
                    for col in columns:
                        value = row[col]
                        converted_value = convert_value_for_postgres(value, col)
                        values.append(converted_value)
                    
                    columns_str = ', '.join(columns)
                    values_str = ', '.join(values)
                    
                    f.write(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n")
                
                f.write(f"\n-- {len(data)} records exported from {table_name}\n\n")
        
        print(f"✅ Exported {table_name} to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return False

def main():
    """Main export function"""
    print("🚀 Exporting MySQL data to SQL files for Supabase")
    print("=" * 60)
    
    # Connect to MySQL
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✅ Connected to MySQL database")
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection error: {e}")
        
        # Try with password prompt
        try:
            password = getpass("Enter MySQL password: ")
            config = MYSQL_CONFIG.copy()
            config['password'] = password
            mysql_conn = mysql.connector.connect(**config)
            print("✅ Connected to MySQL with provided password")
        except mysql.connector.Error as e2:
            print(f"❌ Still failed: {e2}")
            return False
    
    # Create output directory
    output_dir = "supabase_migration_sql"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Tables to export (in order for foreign key constraints)
    tables = ['users', 'patients', 'medical_images', 'audit_logs']
    
    success = True
    
    for table in tables:
        output_file = os.path.join(output_dir, f"{table}.sql")
        if not export_table_to_sql(mysql_conn, table, output_file):
            success = False
    
    # Create combined file
    combined_file = os.path.join(output_dir, "all_data.sql")
    with open(combined_file, 'w', encoding='utf-8') as combined:
        combined.write("-- Combined data export for Supabase migration\n")
        combined.write(f"-- Generated on {datetime.now().isoformat()}\n\n")
        
        for table in tables:
            table_file = os.path.join(output_dir, f"{table}.sql")
            if os.path.exists(table_file):
                with open(table_file, 'r', encoding='utf-8') as f:
                    combined.write(f.read())
                combined.write("\n")
    
    mysql_conn.close()
    
    if success:
        print(f"\n✅ Export completed successfully!")
        print(f"📁 Files created in: {output_dir}")
        print(f"📄 Individual files: {', '.join([f'{t}.sql' for t in tables])}")
        print(f"📄 Combined file: all_data.sql")
        print(f"\n🔄 To import into Supabase:")
        print(f"1. Go to your Supabase dashboard → SQL Editor")
        print(f"2. Copy and paste the contents of 'all_data.sql'")
        print(f"3. Click 'Run' to import all data")
        print(f"\nOr import individual tables using their respective .sql files")
        
    else:
        print(f"\n❌ Export completed with errors")
    
    return success

if __name__ == "__main__":
    main()
