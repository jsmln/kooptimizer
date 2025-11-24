"""
Check and fix gender_enum values
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

def check_enum(conn):
    """Check current enum values"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CHECKING gender_enum VALUES")
    print("="*80)
    
    cursor.execute("""
        SELECT enumlabel
        FROM pg_enum
        WHERE enumtypid = 'gender_enum'::regtype
        ORDER BY enumsortorder
    """)
    
    values = cursor.fetchall()
    print(f"\nCurrent values: {[v[0] for v in values]}")
    
    cursor.close()
    return [v[0] for v in values]

def add_others_value(conn):
    """Add 'others' to gender_enum"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("ADDING 'others' TO gender_enum")
    print("="*80)
    
    try:
        cursor.execute("ALTER TYPE gender_enum ADD VALUE IF NOT EXISTS 'others'")
        conn.commit()
        print("✓ Added 'others' to gender_enum")
        return True
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return False
    finally:
        cursor.close()

def main():
    conn = connect_db()
    if not conn:
        return
    
    try:
        # Check current values
        values = check_enum(conn)
        
        # Add 'others' if not present
        if 'others' not in values:
            add_others_value(conn)
            # Verify
            check_enum(conn)
        else:
            print("\n✓ 'others' already exists in gender_enum")
        
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
