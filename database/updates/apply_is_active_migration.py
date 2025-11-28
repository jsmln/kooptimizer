"""
Script to apply the is_active column migration to cooperatives table
Run this with: python database/updates/apply_is_active_migration.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

def apply_migration():
    """Apply the is_active column migration"""
    print("Applying migration: Add is_active column to cooperatives table...")
    
    try:
        with connection.cursor() as cursor:
            # Check if column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='cooperatives' AND column_name='is_active'
            """)
            
            if cursor.fetchone():
                print("[INFO] Column 'is_active' already exists. Skipping migration.")
                return
            
            # Add is_active column
            print("Adding is_active column...")
            cursor.execute("""
                ALTER TABLE cooperatives 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE
            """)
            
            # Update existing records
            print("Updating existing records...")
            cursor.execute("""
                UPDATE cooperatives 
                SET is_active = TRUE 
                WHERE is_active IS NULL
            """)
            
            # Create index
            print("Creating index...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cooperatives_is_active 
                ON cooperatives(is_active)
            """)
            
            # Add comment
            cursor.execute("""
                COMMENT ON COLUMN cooperatives.is_active IS 
                'Soft delete flag: TRUE = active, FALSE = deactivated, NULL = not set'
            """)
            
            print("[SUCCESS] Migration applied successfully!")
            print("[SUCCESS] Column 'is_active' added to cooperatives table")
            print("[SUCCESS] All existing records set to active (TRUE)")
            print("[SUCCESS] Index created for better query performance")
            
    except Exception as e:
        print(f"[ERROR] Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    apply_migration()

