#!/usr/bin/env python
"""
Script to run the profile_data migration - Fixed version.
This version executes the SQL statements more reliably.
"""
import os
import sys
import django
import re

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
        sql_content = f.read()
    
    # Remove comments and split by semicolons
    # Remove single-line comments
    sql_content = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)
    # Split by semicolons
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    try:
        with connection.cursor() as cursor:
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        print(f"Executing statement {i}/{len(statements)}...")
                        cursor.execute(statement)
                        print(f"  [OK] Statement {i} executed successfully")
                    except Exception as e:
                        error_msg = str(e).lower()
                        # Check if it's a "does not exist" or "already exists" error (which is okay)
                        if 'does not exist' in error_msg or 'already exists' in error_msg or 'duplicate' in error_msg:
                            print(f"  [SKIP] Statement {i} skipped: {str(e)[:80]}")
                        else:
                            print(f"  [ERROR] Statement {i} failed: {str(e)}")
                            # Print the statement for debugging
                            print(f"  Statement was: {statement[:100]}...")
                            raise
        
        connection.commit()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\nMigration failed: {str(e)}")
        connection.rollback()
        return False

if __name__ == '__main__':
    print("Running profile_data migration (Fixed Version)...")
    print("=" * 50)
    success = run_migration()
    print("=" * 50)
    sys.exit(0 if success else 1)

