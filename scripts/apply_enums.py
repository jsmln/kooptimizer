"""
Script to apply missing enum types to the database
"""
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

def apply_enums():
    """Apply missing enum types to the database"""
    
    enums = [
        "CREATE TYPE announcement_type_enum AS ENUM ('sms', 'email')",
        "CREATE TYPE announcement_status_enum AS ENUM ('draft', 'sent', 'scheduled')"
    ]
    
    with connection.cursor() as cursor:
        for enum_sql in enums:
            try:
                # Check if enum already exists
                enum_name = enum_sql.split()[2]
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = %s
                    );
                """, [enum_name])
                
                exists = cursor.fetchone()[0]
                
                if not exists:
                    print(f"Creating enum: {enum_name}")
                    cursor.execute(enum_sql)
                    print(f"✓ Successfully created {enum_name}")
                else:
                    print(f"⚠ Enum {enum_name} already exists, skipping...")
                    
            except Exception as e:
                print(f"✗ Error creating enum: {e}")
                return False
    
    print("\n✓ All enums applied successfully!")
    return True

if __name__ == '__main__':
    apply_enums()
