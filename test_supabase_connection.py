#!/usr/bin/env python3
"""
Test different Supabase connection formats
"""

import psycopg2
from getpass import getpass

# Different possible host formats for your project
possible_hosts = [
    'db.fjmlshmkdaufqkefmixw.supabase.co',
    'fjmlshmkdaufqkefmixw.supabase.co',
    'aws-0-us-east-1.pooler.supabase.com',
    'db.fjmlshmkdaufqkefmixw.pooler.supabase.com'
]

print("Testing Supabase connection with different host formats...")
print("=" * 60)

password = getpass("Enter your Supabase database password: ")

for host in possible_hosts:
    print(f"\nTesting: {host}")
    try:
        conn = psycopg2.connect(
            host=host,
            user='postgres',
            password=password,
            database='postgres',
            port=5432,
            connect_timeout=10
        )
        print(f"✅ SUCCESS: Connected to {host}")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        result = cursor.fetchone()
        print(f"Database version: {result[0]}")
        
        # Check our tables exist
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print(f"Tables found: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        print(f"🎉 Use this host for migration: {host}")
        break
        
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\nOnce you find the working host, update the migration script and run it again.")
