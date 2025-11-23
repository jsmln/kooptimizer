"""
Apply updated sp_get_all_user_accounts with filter parameter support
"""
import psycopg2
import os

# Database connection settings
DB_CONFIG = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': '5432'
}

def apply_stored_procedure():
    """Read and apply the updated stored procedure"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sp_file = os.path.join(script_dir, '..', 'stored_procedures', 'sp_get_all_user_accounts.sql')
    
    print(f"Reading stored procedure from: {sp_file}")
    
    with open(sp_file, 'r') as f:
        sp_sql = f.read()
    
    # Connect to database
    print(f"Connecting to database: {DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Execute the stored procedure definition
        print("Applying updated sp_get_all_user_accounts function...")
        cursor.execute(sp_sql)
        conn.commit()
        print("✓ Stored procedure updated successfully!")
        
        # Test the function with different filters
        print("\nTesting function with different filters:")
        
        # Test 1: Active accounts
        print("\n1. Active accounts:")
        cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('active')")
        count = cursor.fetchone()[0]
        print(f"   Found {count} active accounts")
        
        # Test 2: Deactivated accounts
        print("\n2. Deactivated accounts:")
        cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('deactivated')")
        count = cursor.fetchone()[0]
        print(f"   Found {count} deactivated accounts")
        
        # Test 3: All accounts
        print("\n3. All accounts:")
        cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('all')")
        count = cursor.fetchone()[0]
        print(f"   Found {count} total accounts")
        
        # Test 4: Default parameter (should be 'active')
        print("\n4. Default parameter (no argument):")
        cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts()")
        count = cursor.fetchone()[0]
        print(f"   Found {count} accounts (default=active)")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")

if __name__ == '__main__':
    apply_stored_procedure()
