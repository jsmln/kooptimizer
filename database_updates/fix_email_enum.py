"""
Fix announcement_type_enum to use 'email' instead of 'e-mail'
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

def fix_enum():
    """Add 'email' value to announcement_type_enum and update existing records"""
    
    with connection.cursor() as cursor:
        try:
            # Step 1: Add 'email' value to the enum (if not exists)
            print("Adding 'email' value to announcement_type_enum...")
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum 
                        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                        WHERE pg_type.typname = 'announcement_type_enum' 
                        AND enumlabel = 'email'
                    ) THEN
                        ALTER TYPE announcement_type_enum ADD VALUE 'email';
                    END IF;
                END $$;
            """)
            print("✓ 'email' value added to enum")
            
            # Step 2: Update all existing 'e-mail' records to 'email'
            print("\nUpdating existing 'e-mail' records to 'email'...")
            cursor.execute("""
                UPDATE announcements 
                SET type = 'email'::announcement_type_enum 
                WHERE type = 'e-mail'::announcement_type_enum;
            """)
            updated_count = cursor.rowcount
            print(f"✓ Updated {updated_count} records from 'e-mail' to 'email'")
            
            # Step 3: Note about removing 'e-mail' (optional - requires recreating enum)
            print("\n⚠ NOTE: The 'e-mail' value still exists in the enum.")
            print("   PostgreSQL doesn't support removing enum values directly.")
            print("   Both 'email' and 'e-mail' are now valid, but the system uses 'email'.")
            
            print("\n✓ Fix completed successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    fix_enum()
