#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path('/app')
load_dotenv(ROOT_DIR / 'backend' / '.env')

DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Connecting to database...")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = cursor.fetchall()
print('Existing tables:')
for table in tables:
    print(f'  - {table[0]}')

conn.close()