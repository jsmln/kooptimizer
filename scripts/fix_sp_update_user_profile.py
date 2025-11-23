"""
Apply fix to sp_update_user_profile
This script will drop the old FUNCTION version and ensure only the PROCEDURE version exists
"""

import psycopg2

# Database connection parameters
DB_PARAMS = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

def connect_db():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        print("✓ Connected to kooptimizer_db2")
        return conn
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def apply_fix(conn):
    """Apply the fix for sp_update_user_profile"""
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*80)
        print("APPLYING FIX: sp_update_user_profile")
        print("="*80)
        
        # Read the fix script
        with open('stored_procedures/fix_sp_update_user_profile.sql', 'r') as f:
            fix_sql = f.read()
        
        # Execute the fix
        cursor.execute(fix_sql)
        conn.commit()
        
        print("✓ Fix applied successfully")
        
        # Verify the fix
        cursor.execute("""
            SELECT routine_type, data_type
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_name = 'sp_update_user_profile'
        """)
        results = cursor.fetchall()
        
        print(f"\nVerification - Found {len(results)} definition(s):")
        for row in results:
            print(f"  Type: {row[0]}, Returns: {row[1]}")
        
        if len(results) == 1 and results[0][0] == 'PROCEDURE':
            print("\n✓ SUCCESS: sp_update_user_profile is now a PROCEDURE only")
            return True
        else:
            print("\n✗ WARNING: Unexpected state after fix")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to apply fix: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()

def main():
    conn = connect_db()
    if not conn:
        return
    
    try:
        success = apply_fix(conn)
        if success:
            print("\n" + "="*80)
            print("FIX COMPLETED SUCCESSFULLY")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("FIX FAILED - Manual intervention may be required")
            print("="*80)
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
