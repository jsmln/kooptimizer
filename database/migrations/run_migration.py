#!/usr/bin/env python
"""
Script to run the profile_data migration.
Make sure you're in the project root directory when running this.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

def run_migration():
    """Execute the SQL migration file."""
    # Get the path to the SQL file
    migration_file = os.path.join(
        os.path.dirname(__file__),
        'add_report_year_to_profile_data.sql'
    )
    
    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found at {migration_file}")
        return False
    
    # Read the SQL file
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Split by semicolons and execute each statement
    # (Some statements might span multiple lines)
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✓ Executed: {statement[:50]}...")
                    except Exception as e:
                        # Some statements might fail if already executed (IF NOT EXISTS)
                        if 'already exists' in str(e).lower() or 'does not exist' in str(e).lower():
                            print(f"⚠ Skipped (already exists/doesn't exist): {statement[:50]}...")
                        else:
                            print(f"✗ Error executing: {statement[:50]}...")
                            print(f"  Error: {str(e)}")
                            raise
        
        connection.commit()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        connection.rollback()
        return False

if __name__ == '__main__':
    print("Running profile_data migration...")
    print("=" * 50)
    success = run_migration()
    print("=" * 50)
    sys.exit(0 if success else 1)

