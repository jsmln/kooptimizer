import os
import sys

# Ensure project path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')

import django
django.setup()

from django.db import connection

def apply_sp_get_all_user_accounts():
    sql_path = os.path.join(BASE_DIR, 'stored_procedures', 'sp_get_all_user_accounts.sql')
    print(f"Applying {sql_path}...")
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        with connection.cursor() as cur:
            connection.autocommit = True
            # Drop existing function first to avoid conflicts
            print("Dropping old sp_get_all_user_accounts function...")
            cur.execute('DROP FUNCTION IF EXISTS sp_get_all_user_accounts(VARCHAR) CASCADE;')
            
            # Apply the new version
            print("Creating updated sp_get_all_user_accounts function...")
            cur.execute(sql)
            
            print("✓ Successfully applied sp_get_all_user_accounts.sql")
            
            # Test it
            print("\nTesting the updated function...")
            cur.execute("SELECT * FROM sp_get_all_user_accounts('active') LIMIT 1")
            result = cur.fetchone()
            if result:
                print(f"✓ Function working! Sample result has {len(result)} columns")
                print(f"  Columns: formatted_id, user_id, profile_id, fullname, email, mobile_number, position, coop_name, account_type, is_active, created_at, updated_at")
            else:
                print("⚠ No active users found in database")
                
    except Exception as e:
        print(f"✗ Error applying stored procedure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    apply_sp_get_all_user_accounts()
    print("\n✓ Done!")
