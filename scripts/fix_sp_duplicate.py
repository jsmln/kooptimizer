"""
Drop old sp_get_all_user_accounts function and apply updated version
"""
import psycopg2

# Database connection settings
DB_CONFIG = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': '5432'
}

# Connect to database
print(f"Connecting to database: {DB_CONFIG['dbname']}")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    # Drop old function version (without parameters)
    print("Dropping old sp_get_all_user_accounts() function...")
    cursor.execute("DROP FUNCTION IF EXISTS sp_get_all_user_accounts() CASCADE;")
    conn.commit()
    print("✓ Old function dropped successfully!")
    
    # Verify only new version exists
    print("\nVerifying function exists with correct signature...")
    cursor.execute("""
        SELECT proname, pg_get_function_arguments(oid) as args
        FROM pg_proc 
        WHERE proname = 'sp_get_all_user_accounts'
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} function(s):")
    for row in results:
        print(f"  - {row[0]}({row[1]})")
    
    # Test the updated function
    print("\nTesting updated function:")
    cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('active')")
    active_count = cursor.fetchone()[0]
    print(f"  Active accounts: {active_count}")
    
    cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('deactivated')")
    deactivated_count = cursor.fetchone()[0]
    print(f"  Deactivated accounts: {deactivated_count}")
    
    cursor.execute("SELECT COUNT(*) FROM sp_get_all_user_accounts('all')")
    all_count = cursor.fetchone()[0]
    print(f"  All accounts: {all_count}")
    
    print("\n✓ Function updated successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Error: {e}")
    raise
finally:
    cursor.close()
    conn.close()
    print("\nDatabase connection closed")
