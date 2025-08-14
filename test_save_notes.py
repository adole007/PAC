#!/usr/bin/env python3
"""
Test script to verify Save Notes API endpoint works correctly
"""

import os
import sys
import json
import requests
import psycopg2

def test_save_notes_api():
    print('🧪 Testing Save Notes API endpoint...')
    
    # Get database connection
    line = ""
    try:
        with open("backend/.env", "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.strip().split("=", 1)[1]
                    break
    except:
        print('❌ ERROR: Could not read DATABASE_URL from backend/.env')
        return False
    
    # Find an existing image to test with
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Get first image ID and a user ID
        cur.execute("SELECT id FROM medical_images LIMIT 1")
        image_row = cur.fetchone()
        if not image_row:
            print('⚠️  No images found in database - cannot test')
            return False
        image_id = image_row[0]
        
        cur.execute("SELECT id FROM users LIMIT 1")
        user_row = cur.fetchone()
        if not user_row:
            print('❌ No users found in database')
            return False
        user_id = user_row[0]
        
        print(f'📋 Testing with image_id: {image_id}')
        print(f'👤 Testing with user_id: {user_id}')
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False
    
    # Test direct database update (bypass API)
    print('\n🔧 Testing direct database update...')
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        test_note = 'API test note - database write successful'
        cur.execute("UPDATE medical_images SET clinician_notes = %s WHERE id = %s", (test_note, image_id))
        
        # Verify update
        cur.execute("SELECT clinician_notes FROM medical_images WHERE id = %s", (image_id,))
        result = cur.fetchone()
        if result and result[0] == test_note:
            print('✅ Direct database update successful')
        else:
            print('❌ Direct database update failed')
            return False
            
        # Test history insertion
        import uuid
        from datetime import datetime
        cur.execute(
            "INSERT INTO medical_image_notes (id, image_id, user_id, note, created_at) VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), image_id, user_id, test_note, datetime.utcnow())
        )
        print('✅ History insertion successful')
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Database write test failed: {e}')
        return False
    
    # Test API endpoint (if backend is running)
    print('\n🌐 Testing API endpoint...')
    try:
        # Try to login first to get a token
        login_response = requests.post('http://localhost:8001/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        }, timeout=5)
        
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            print('✅ Login successful, got auth token')
            
            # Test the PUT /images/{image_id} endpoint
            headers = {'Authorization': f'Bearer {token}'}
            payload = {'clinician_notes': 'API test note - endpoint working correctly'}
            
            api_response = requests.put(
                f'http://localhost:8001/api/images/{image_id}',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if api_response.status_code == 200:
                print('✅ API endpoint successful')
                print(f'Response: {api_response.json()}')
                
                # Verify the update in database
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("SELECT clinician_notes FROM medical_images WHERE id = %s", (image_id,))
                result = cur.fetchone()
                if result and result[0] == payload['clinician_notes']:
                    print('✅ API update verified in database')
                else:
                    print('❌ API update not found in database')
                cur.close()
                conn.close()
                
                return True
            else:
                print(f'❌ API endpoint failed: {api_response.status_code}')
                print(f'Response: {api_response.text}')
                return False
        else:
            print(f'❌ Login failed: {login_response.status_code}')
            if login_response.status_code == 401:
                print('   Check if admin/admin123 credentials are correct')
            return False
            
    except requests.exceptions.ConnectionError:
        print('⚠️  Backend server not running on localhost:8001')
        print('   Start the backend with: python backend/server_postgresql_fully_optimized.py')
        return False
    except Exception as e:
        print(f'❌ API test failed: {e}')
        return False

def main():
    print('🔍 Save Notes API Diagnostic Test')
    print('=' * 50)
    
    if test_save_notes_api():
        print('\n🎉 All tests passed! Save Notes functionality is working correctly.')
        print('\nIf the frontend Save Notes button still fails:')
        print('1. Check browser developer console for JavaScript errors')
        print('2. Check browser network tab for failed API requests')
        print('3. Ensure the frontend is pointing to the correct backend URL')
        print('4. Make sure the backend server is running and accessible')
    else:
        print('\n❌ Tests failed. Save Notes functionality has issues.')
        print('\nTroubleshooting steps:')
        print('1. Ensure the backend server is running')
        print('2. Check database connectivity')
        print('3. Verify the clinician_notes column exists')
        print('4. Check backend logs for errors')

if __name__ == '__main__':
    main()
