#!/usr/bin/env python
"""
Apply the updated sp_get_announcement_details stored procedure
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection


def apply_stored_procedure():
    """Apply the updated stored procedure"""
    sql_file = os.path.join(os.path.dirname(__file__), 'update_sp_get_announcement_details_v2.sql')
    
    print("\n" + "="*60)
    print("APPLY STORED PROCEDURE UPDATE")
    print("="*60)
    print(f"Reading: {sql_file}\n")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            print("✓ Stored procedure sp_get_announcement_details updated successfully!")
            
            # Test the procedure
            cursor.execute("SELECT COUNT(*) FROM announcements LIMIT 1")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT announcement_id FROM announcements LIMIT 1")
                test_id = cursor.fetchone()[0]
                
                print(f"\n🔍 Testing with announcement_id={test_id}...")
                cursor.execute(f"SELECT * FROM sp_get_announcement_details({test_id})")
                result = cursor.fetchone()
                
                if result:
                    print("✓ Stored procedure is working!")
                    print(f"  - Title: {result[1] if len(result) > 1 else 'N/A'}")
                    print(f"  - Has attachments_json field: {'Yes' if len(result) > 10 else 'No'}")
                else:
                    print("⚠ No result returned (announcement might not exist)")
            else:
                print("\nℹ No announcements in database to test with")
                
    except Exception as e:
        print(f"\n❌ Error applying stored procedure: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    return True


if __name__ == '__main__':
    success = apply_stored_procedure()
    sys.exit(0 if success else 1)
