#!/usr/bin/env python3
"""
Database Migration Script: Add clinician_notes column and medical_image_notes history table
"""

import os
import sys
import uuid
import traceback
import psycopg2

def main():
    print('🔧 Starting database migration for clinician_notes...')
    
    try:
        # Get database URL
        url = os.environ.get('DATABASE_URL')
        if not url:
            print('❌ ERROR: DATABASE_URL environment variable not set!')
            sys.exit(1)
        
        print(f'🔗 Connecting to database: {url.split("@")[-1] if "@" in url else "local"}')
        
        # Connect to database
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check current state
        print('📋 Checking current database state...')
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('medical_images', 'users')")
        tables = [row[0] for row in cur.fetchall()]
        print(f'   Found tables: {tables}')
        
        if 'medical_images' not in tables:
            print('❌ ERROR: medical_images table not found!')
            sys.exit(1)
        
        # Check if clinician_notes column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='medical_images' AND column_name='clinician_notes'")
        has_col = bool(cur.fetchone())
        print(f'   clinician_notes column exists: {has_col}')
        
        # Add clinician_notes column if it doesn't exist
        if not has_col:
            print('➕ Adding clinician_notes column...')
            cur.execute("ALTER TABLE medical_images ADD COLUMN clinician_notes TEXT")
            print('   ✅ clinician_notes column added successfully')
        else:
            print('   ✅ clinician_notes column already exists')
        
        # Check if medical_image_notes table exists
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='medical_image_notes'")
        has_hist_table = bool(cur.fetchone())
        print(f'   medical_image_notes table exists: {has_hist_table}')
        
        # Create medical_image_notes table if it doesn't exist
        if not has_hist_table:
            print('🏗️ Creating medical_image_notes history table...')
            cur.execute("""
            CREATE TABLE medical_image_notes (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                image_id UUID NOT NULL,
                user_id UUID NOT NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_image FOREIGN KEY (image_id) REFERENCES medical_images(id) ON DELETE CASCADE,
                CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            print('   ✅ medical_image_notes table created successfully')
            
            # Create indexes
            print('📊 Creating indexes...')
            cur.execute("CREATE INDEX idx_image_notes_image_id ON medical_image_notes(image_id)")
            cur.execute("CREATE INDEX idx_image_notes_user_id ON medical_image_notes(user_id)")
            cur.execute("CREATE INDEX idx_image_notes_created_at ON medical_image_notes(created_at)")
            print('   ✅ Indexes created successfully')
        else:
            print('   ✅ medical_image_notes table already exists')
        
        # Verify final state
        print('🔍 Verifying final state...')
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='medical_images' AND column_name='clinician_notes'")
        final_col_check = bool(cur.fetchone())
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='medical_image_notes'")
        final_table_check = bool(cur.fetchone())
        
        print(f'   Final verification - clinician_notes column: {final_col_check}')
        print(f'   Final verification - medical_image_notes table: {final_table_check}')
        
        if final_col_check and final_table_check:
            print('\n🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!')
            print('   The clinician_notes column and history table are now ready for use.')
        else:
            print('\n❌ Migration verification failed!')
            sys.exit(1)
        
        # Show current table structure
        print('\n📋 Current medical_images table structure:')
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='medical_images' ORDER BY ordinal_position")
        for row in cur.fetchall():
            marker = ' ← NEW' if row[0] == 'clinician_notes' else ''
            print(f'   {row[0]} ({row[1]}){marker}')
        
        # Test the new column with a sample update
        print('\n🧪 Testing clinician_notes column...')
        cur.execute("SELECT id FROM medical_images LIMIT 1")
        test_image = cur.fetchone()
        if test_image:
            test_note = 'Migration test note - column working correctly'
            cur.execute("UPDATE medical_images SET clinician_notes = %s WHERE id = %s", (test_note, test_image[0]))
            cur.execute("SELECT clinician_notes FROM medical_images WHERE id = %s", (test_image[0],))
            retrieved_note = cur.fetchone()[0]
            if retrieved_note == test_note:
                print('   ✅ Column write/read test passed')
                # Clean up test
                cur.execute("UPDATE medical_images SET clinician_notes = NULL WHERE id = %s", (test_image[0],))
            else:
                print('   ❌ Column write/read test failed')
        else:
            print('   ⚠️ No images found for testing (normal for empty database)')
        
        cur.close()
        conn.close()
        print('\n🔌 Database connection closed.')
        print('✨ Migration complete! You can now use the Save Notes feature.')
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        print('\n📋 Full traceback:')
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
