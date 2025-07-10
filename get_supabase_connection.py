#!/usr/bin/env python3
"""
Helper script to get your Supabase connection details
"""

print("🔍 Finding your Supabase connection details")
print("=" * 50)
print()
print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
print("2. Select your project")
print("3. Go to Settings → Database (in the left sidebar)")
print("4. Scroll down to find 'Connection Info' section")
print()
print("You'll see something like:")
print("Host: db.abcdefghijklmnop.supabase.co")
print("Database: postgres")
print("Port: 5432")
print("User: postgres")
print("Password: [your password]")
print()
print("Copy the HOST value (starts with 'db.' and ends with '.supabase.co')")
print("This is what you need to enter when running the migration script.")
print()
print("Example correct format:")
print("✅ Good: db.abcdefghijklmnop.supabase.co")
print("❌ Bad: https://supabase.com/dashboard/project/...")
print()
print("Once you have the correct host, run the migration again:")
print("python migrate_mysql_to_supabase.py")
