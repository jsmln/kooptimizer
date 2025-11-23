"""
Final fix for sp_update_user_profile - drop by OID
"""

import psycopg2

DB_PARAMS = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        print("✓ Connected to kooptimizer_db2")
        return conn
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def drop_all_by_oid(conn):
    """Drop all versions by OID"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DROPPING ALL sp_update_user_profile BY OID")
    print("="*80)
    
    try:
        # Get all OIDs
        cursor.execute("""
            SELECT p.oid, pg_catalog.pg_get_function_identity_arguments(p.oid) as args
            FROM pg_catalog.pg_proc p
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
            WHERE p.proname = 'sp_update_user_profile'
            AND n.nspname = 'public'
        """)
        
        oids = cursor.fetchall()
        print(f"Found {len(oids)} version(s) to drop\n")
        
        for oid, args in oids:
            # Use the name with explicit signature
            try:
                cursor.execute(f"DROP PROCEDURE public.sp_update_user_profile({args}) CASCADE")
                print(f"✓ Dropped procedure: sp_update_user_profile({args[:60]}...)")
            except Exception as e:
                print(f"  Failed to drop: {e}")
        
        conn.commit()
        print("\n✓ All versions dropped")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()

def create_final_version(conn):
    """Create the final correct version"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CREATING FINAL VERSION")
    print("="*80)
    
    try:
        # Read from the SQL file
        with open('stored_procedures/sp_update_user_profile.sql', 'r') as f:
            sql = f.read()
        
        cursor.execute(sql)
        conn.commit()
        print("✓ Created procedure from sp_update_user_profile.sql")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()

def verify(conn):
    """Verify final state"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            pg_catalog.pg_get_function_identity_arguments(p.oid) as arguments,
            CASE 
                WHEN p.prokind = 'f' THEN 'FUNCTION'
                WHEN p.prokind = 'p' THEN 'PROCEDURE'
            END as type
        FROM pg_catalog.pg_proc p
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE p.proname = 'sp_update_user_profile'
        AND n.nspname = 'public'
    """)
    
    results = cursor.fetchall()
    print(f"\nFound {len(results)} version(s):\n")
    
    for row in results:
        print(f"  {row[1]}: sp_update_user_profile({row[0]})")
    
    cursor.close()
    
    if len(results) == 1 and results[0][1] == 'PROCEDURE':
        print("\n✓ SUCCESS: Single PROCEDURE version exists")
        return True
    else:
        print(f"\n✗ WARNING: Expected 1 PROCEDURE, found {len(results)}")
        return False

def main():
    conn = connect_db()
    if not conn:
        return
    
    try:
        # Drop all versions
        if drop_all_by_oid(conn):
            # Create the correct version
            if create_final_version(conn):
                # Verify
                verify(conn)
        
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
