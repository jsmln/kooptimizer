"""
Check and clean sp_update_user_profile duplicates
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

def check_all_versions(conn):
    """Check all versions of sp_update_user_profile"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CHECKING ALL VERSIONS OF sp_update_user_profile")
    print("="*80)
    
    # Get detailed info about all versions
    cursor.execute("""
        SELECT 
            p.proname as name,
            pg_catalog.pg_get_function_identity_arguments(p.oid) as arguments,
            CASE 
                WHEN p.prokind = 'f' THEN 'FUNCTION'
                WHEN p.prokind = 'p' THEN 'PROCEDURE'
                ELSE 'OTHER'
            END as type,
            pg_catalog.pg_get_function_result(p.oid) as return_type
        FROM pg_catalog.pg_proc p
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE p.proname = 'sp_update_user_profile'
        AND n.nspname = 'public'
    """)
    
    results = cursor.fetchall()
    print(f"\nFound {len(results)} version(s):\n")
    
    for i, row in enumerate(results, 1):
        print(f"{i}. {row[2]}: {row[0]}({row[1]})")
        print(f"   Returns: {row[3]}")
        print()
    
    cursor.close()
    return results

def drop_all_versions(conn):
    """Drop all versions of sp_update_user_profile"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DROPPING ALL VERSIONS")
    print("="*80)
    
    try:
        # Drop all possible versions
        drop_commands = [
            "DROP FUNCTION IF EXISTS public.sp_update_user_profile(integer, text, text, text, text, text, integer, integer[]) CASCADE",
            "DROP FUNCTION IF EXISTS public.sp_update_user_profile(integer, character varying, character varying, character varying, character varying, character varying, integer, integer[]) CASCADE",
            "DROP PROCEDURE IF EXISTS public.sp_update_user_profile(integer, character varying, character varying, character varying, gender_enum, character varying, integer, integer[]) CASCADE",
            "DROP PROCEDURE IF EXISTS public.sp_update_user_profile(integer, character varying, character varying, character varying, character varying, character varying, integer, integer[]) CASCADE",
        ]
        
        for cmd in drop_commands:
            try:
                cursor.execute(cmd)
                print(f"✓ Executed: {cmd[:80]}...")
            except Exception as e:
                print(f"  (Skipped, probably doesn't exist)")
        
        conn.commit()
        print("\n✓ All drop commands executed")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error dropping: {e}")
    finally:
        cursor.close()

def create_correct_version(conn):
    """Create the correct PROCEDURE version"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CREATING CORRECT PROCEDURE VERSION")
    print("="*80)
    
    try:
        sql = """
CREATE OR REPLACE PROCEDURE public.sp_update_user_profile(
    IN p_user_id integer,
    IN p_fullname character varying,
    IN p_email character varying,
    IN p_mobile_number character varying,
    IN p_gender character varying,
    IN p_position character varying,
    IN p_officer_coop_id integer DEFAULT NULL,
    IN p_staff_coop_ids integer[] DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_role user_role_enum;
    v_staff_id INTEGER;
    v_gender_enum gender_enum;
BEGIN
    -- Cast string gender to enum
    v_gender_enum := CASE 
        WHEN p_gender IS NOT NULL THEN p_gender::gender_enum 
        ELSE NULL 
    END;

    -- Get the user's role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;

    -- Update the username (email)
    UPDATE users SET username = p_email, updated_at = NOW() WHERE user_id = p_user_id;

    -- Update the specific profile
    IF v_role = 'admin'::user_role_enum THEN
        UPDATE admin
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id;
        
    ELSIF v_role = 'staff'::user_role_enum THEN
        UPDATE staff
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id
        RETURNING staff_id INTO v_staff_id;
        
        -- Un-assign all current coops from this staff
        UPDATE cooperatives SET staff_id = NULL WHERE staff_id = v_staff_id;
        
        -- Re-assign the new list of coops
        IF p_staff_coop_ids IS NOT NULL AND array_length(p_staff_coop_ids, 1) > 0 THEN
            UPDATE cooperatives
            SET staff_id = v_staff_id
            WHERE coop_id = ANY(p_staff_coop_ids);
        END IF;

    ELSIF v_role = 'officer'::user_role_enum THEN
        UPDATE officers
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position, 
            coop_id = p_officer_coop_id
        WHERE user_id = p_user_id;
    END IF;

END;
$$;
        """
        
        cursor.execute(sql)
        conn.commit()
        print("✓ Created PROCEDURE successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating procedure: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()

def main():
    conn = connect_db()
    if not conn:
        return
    
    try:
        # Check what exists
        check_all_versions(conn)
        
        # Drop all versions
        drop_all_versions(conn)
        
        # Create correct version
        create_correct_version(conn)
        
        # Verify final state
        print("\n" + "="*80)
        print("FINAL STATE")
        print("="*80)
        results = check_all_versions(conn)
        
        if len(results) == 1 and 'PROCEDURE' in str(results[0]):
            print("✓ SUCCESS: Single PROCEDURE version exists")
        else:
            print("✗ WARNING: Unexpected final state")
        
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
