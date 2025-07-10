import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv('../.env')

DATABASE_URL = os.environ.get('DATABASE_URL')

def test_database_images():
    """Test database connection and check for images"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get basic info about images
        cursor.execute("""
            SELECT id, patient_id, modality, original_filename, 
                   LENGTH(image_data) as image_size, 
                   LENGTH(thumbnail_data) as thumb_size 
            FROM medical_images 
            LIMIT 5;
        """)
        
        images = cursor.fetchall()
        print(f"Found {len(images)} images in database:")
        
        for img in images:
            print(f"  ID: {img['id']}")
            print(f"  Patient: {img['patient_id']}")
            print(f"  Modality: {img['modality']}")
            print(f"  Filename: {img['original_filename']}")
            print(f"  Image size: {img['image_size']} bytes")
            print(f"  Thumbnail size: {img['thumb_size']} bytes")
            print("  ---")
        
        if images:
            # Test if we can decode one image
            first_image = images[0]
            cursor.execute("SELECT image_data FROM medical_images WHERE id = %s", (first_image['id'],))
            result = cursor.fetchone()
            
            if result and result['image_data']:
                try:
                    decoded_data = base64.b64decode(result['image_data'])
                    print(f"✅ Successfully decoded image data: {len(decoded_data)} bytes")
                    
                    # Check if it starts with JPEG header
                    if decoded_data[:3] == b'\xff\xd8\xff':
                        print("✅ Image appears to be JPEG format")
                    else:
                        print("⚠️  Image might not be JPEG format")
                        print(f"First 10 bytes: {decoded_data[:10]}")
                    
                except Exception as e:
                    print(f"❌ Failed to decode image data: {e}")
            else:
                print("❌ No image data found")
        
        conn.close()
        return images
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def check_users():
    """Check users in database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # First check table schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        columns = cursor.fetchall()
        print("User table columns:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
        # Then get users
        cursor.execute("SELECT username, role, hashed_password FROM users LIMIT 10;")
        users = cursor.fetchall()
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
            if 'hashed_password' in user and user['hashed_password']:
                print(f"    Password hash: {user['hashed_password'][:30]}...")
        
        conn.close()
        return users
    except Exception as e:
        print(f"Error checking users: {e}")
        return []

if __name__ == "__main__":
    test_database_images()
    print("\n" + "="*50 + "\n")
    check_users()
