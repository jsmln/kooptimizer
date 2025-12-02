"""
Test script to check all CRUD functionalities in account_management
This script will connect to the database and verify:
1. CREATE - User creation with sp_create_user_profile
2. READ - User retrieval with sp_get_all_user_accounts and sp_get_user_details
3. UPDATE - User update with sp_update_user_profile
4. DELETE/DEACTIVATE - User deactivation with sp_deactivate_user
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json
from datetime import datetime

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
        print("✓ Successfully connected to kooptimizer_db2")
        return conn
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def check_stored_procedures(conn):
    """Check if all required stored procedures exist"""
    print("\n" + "="*80)
    print("CHECKING STORED PROCEDURES")
    print("="*80)
    
    procedures = [
        ('sp_create_user_profile', 'function'),
        ('sp_get_all_user_accounts', 'function'),
        ('sp_get_user_details', 'function'),
        ('sp_update_user_profile', 'procedure'),
        ('sp_deactivate_user', 'procedure')
    ]
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    results = {}
    
    for proc_name, proc_type in procedures:
        query = f"""
            SELECT 
                routine_name,
                routine_type,
                data_type as return_type
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_name = '{proc_name}'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            print(f"✓ {proc_name} exists (type: {result['routine_type']}, returns: {result['return_type']})")
            results[proc_name] = True
        else:
            print(f"✗ {proc_name} NOT FOUND")
            results[proc_name] = False
    
    cursor.close()
    return results

def check_tables(conn):
    """Check if all required tables exist and their structure"""
    print("\n" + "="*80)
    print("CHECKING DATABASE TABLES")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check main tables
    tables = ['users', 'admin', 'staff', 'officers', 'cooperatives']
    
    for table in tables:
        query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{table}'
            ORDER BY ordinal_position
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        
        if columns:
            print(f"\n✓ Table: {table}")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable} {default}")
        else:
            print(f"✗ Table {table} NOT FOUND")
    
    cursor.close()

def test_create_user(conn):
    """Test CREATE operation - sp_create_user_profile"""
    print("\n" + "="*80)
    print("TESTING CREATE OPERATION (sp_create_user_profile)")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Test data
    test_users = [
        {
            'username': f'test_admin_{datetime.now().strftime("%Y%m%d%H%M%S")}@test.com',
            'password_hash': 'hashed_password_123',
            'role': 'admin',
            'fullname': 'Test Admin User',
            'email': f'test_admin_{datetime.now().strftime("%Y%m%d%H%M%S")}@test.com',
            'mobile': '09123456789',
            'gender': 'male',
            'position': 'Test Admin Position',
            'officer_coop_id': None,
            'staff_coop_ids': None
        },
        {
            'username': f'test_staff_{datetime.now().strftime("%Y%m%d%H%M%S")}@test.com',
            'password_hash': 'hashed_password_456',
            'role': 'staff',
            'fullname': 'Test Staff User',
            'email': f'test_staff_{datetime.now().strftime("%Y%m%d%H%M%S")}@test.com',
            'mobile': '09987654321',
            'gender': 'female',
            'position': 'Test Staff Position',
            'officer_coop_id': None,
            'staff_coop_ids': []
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            query = """
                SELECT * FROM sp_create_user_profile(
                    %s::varchar,           -- p_username
                    %s::varchar,           -- p_password_hash
                    %s::user_role_enum,    -- p_role
                    %s::varchar,           -- p_fullname
                    %s::varchar,           -- p_email
                    %s::varchar,           -- p_mobile_number
                    %s::gender_enum,       -- p_gender
                    %s::varchar,           -- p_position
                    %s::integer,           -- p_officer_coop_id
                    %s::integer[]          -- p_staff_coop_ids
                )
            """
            cursor.execute(query, [
                user_data['username'],
                user_data['password_hash'],
                user_data['role'],
                user_data['fullname'],
                user_data['email'],
                user_data['mobile'],
                user_data['gender'],
                user_data['position'],
                user_data['officer_coop_id'],
                user_data['staff_coop_ids']
            ])
            result = cursor.fetchone()
            conn.commit()
            
            print(f"\n✓ Created {user_data['role']} user:")
            print(f"  User ID: {result['new_user_id']}")
            print(f"  Profile ID: {result['new_profile_id']}")
            print(f"  Formatted ID: {result['formatted_id']}")
            print(f"  Role: {result['user_role']}")
            
            created_users.append({
                'user_id': result['new_user_id'],
                'profile_id': result['new_profile_id'],
                'role': user_data['role'],
                'email': user_data['email']
            })
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Failed to create {user_data['role']} user: {e}")
    
    cursor.close()
    return created_users

def test_read_all_users(conn):
    """Test READ operation - sp_get_all_user_accounts"""
    print("\n" + "="*80)
    print("TESTING READ ALL OPERATION (sp_get_all_user_accounts)")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM sp_get_all_user_accounts()")
        users = cursor.fetchall()
        
        print(f"\n✓ Retrieved {len(users)} users from database")
        
        # Group by account type
        admins = [u for u in users if u['account_type'] == 'Admin']
        staff = [u for u in users if u['account_type'] == 'Staff']
        officers = [u for u in users if u['account_type'] == 'Officer']
        
        print(f"\n  Admins: {len(admins)}")
        print(f"  Staff: {len(staff)}")
        print(f"  Officers: {len(officers)}")
        
        # Show sample data
        if users:
            print("\n  Sample user data:")
            sample = users[0]
            for key, value in sample.items():
                print(f"    {key}: {value}")
        
        return users
        
    except Exception as e:
        print(f"✗ Failed to retrieve users: {e}")
        return []
    finally:
        cursor.close()

def test_read_user_details(conn, user_id):
    """Test READ operation - sp_get_user_details"""
    print("\n" + "="*80)
    print(f"TESTING READ DETAILS OPERATION (sp_get_user_details) - User ID: {user_id}")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT sp_get_user_details(%s) as details", [user_id])
        result = cursor.fetchone()
        
        if result and result['details']:
            details = result['details']
            print(f"\n✓ Retrieved user details:")
            print(json.dumps(details, indent=2))
            return details
        else:
            print(f"✗ No details found for user_id: {user_id}")
            return None
            
    except Exception as e:
        print(f"✗ Failed to retrieve user details: {e}")
        return None
    finally:
        cursor.close()

def test_update_user(conn, user_id, role):
    """Test UPDATE operation - sp_update_user_profile"""
    print("\n" + "="*80)
    print(f"TESTING UPDATE OPERATION (sp_update_user_profile) - User ID: {user_id}")
    print("="*80)
    
    cursor = conn.cursor()
    
    try:
        # Updated data
        updated_name = f"Updated User {datetime.now().strftime('%H%M%S')}"
        updated_email = f"updated_{user_id}@test.com"
        updated_mobile = "09111222333"
        updated_gender = "others"
        updated_position = "Updated Position"
        
        query = """
            CALL sp_update_user_profile(
                %s::integer,
                %s::varchar,
                %s::varchar,
                %s::varchar,
                %s::varchar,
                %s::varchar,
                %s::integer,
                %s::integer[]
            )
        """
        cursor.execute(query, [
            user_id,
            updated_name,
            updated_email,
            updated_mobile,
            updated_gender,
            updated_position,
            None,  # officer_coop_id
            None   # staff_coop_ids
        ])
        conn.commit()
        
        print(f"✓ Updated user successfully")
        print(f"  New name: {updated_name}")
        print(f"  New email: {updated_email}")
        print(f"  New mobile: {updated_mobile}")
        print(f"  New position: {updated_position}")
        
        # Verify the update
        cursor.execute("SELECT sp_get_user_details(%s) as details", [user_id])
        result = cursor.fetchone()
        if result and result[0]:
            print(f"\n  Verification - Updated details:")
            print(json.dumps(result[0], indent=2))
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to update user: {e}")
        return False
    finally:
        cursor.close()

def test_deactivate_user(conn, user_id):
    """Test DELETE/DEACTIVATE operation - sp_deactivate_user"""
    print("\n" + "="*80)
    print(f"TESTING DEACTIVATE OPERATION (sp_deactivate_user) - User ID: {user_id}")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check user status before deactivation
        cursor.execute("SELECT is_active FROM users WHERE user_id = %s", [user_id])
        before = cursor.fetchone()
        print(f"  Before: is_active = {before['is_active']}")
        
        # Deactivate user
        cursor.execute("CALL sp_deactivate_user(%s)", [user_id])
        conn.commit()
        
        # Check user status after deactivation
        cursor.execute("SELECT is_active FROM users WHERE user_id = %s", [user_id])
        after = cursor.fetchone()
        print(f"  After: is_active = {after['is_active']}")
        
        if not after['is_active']:
            print(f"✓ User deactivated successfully")
            return True
        else:
            print(f"✗ User deactivation failed - is_active still True")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to deactivate user: {e}")
        return False
    finally:
        cursor.close()

def cleanup_test_users(conn, created_users):
    """Clean up test users created during testing"""
    print("\n" + "="*80)
    print("CLEANING UP TEST DATA")
    print("="*80)
    
    cursor = conn.cursor()
    
    for user in created_users:
        try:
            user_id = user['user_id']
            role = user['role']
            
            # Delete from role-specific table first
            if role == 'admin':
                cursor.execute("DELETE FROM admin WHERE user_id = %s", [user_id])
            elif role == 'staff':
                cursor.execute("DELETE FROM staff WHERE user_id = %s", [user_id])
            elif role == 'officer':
                cursor.execute("DELETE FROM officers WHERE user_id = %s", [user_id])
            
            # Delete from users table
            cursor.execute("DELETE FROM users WHERE user_id = %s", [user_id])
            conn.commit()
            
            print(f"✓ Cleaned up {role} user (user_id: {user_id})")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Failed to clean up user {user_id}: {e}")
    
    cursor.close()

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("ACCOUNT MANAGEMENT CRUD FUNCTIONALITY TEST")
    print("Database: kooptimizer_db2")
    print("="*80)
    
    # Connect to database
    conn = connect_db()
    if not conn:
        return
    
    try:
        # 1. Check stored procedures
        sp_results = check_stored_procedures(conn)
        
        # 2. Check tables
        check_tables(conn)
        
        # 3. Test CREATE
        created_users = test_create_user(conn)
        
        if created_users:
            # 4. Test READ ALL
            all_users = test_read_all_users(conn)
            
            # 5. Test READ DETAILS
            for user in created_users:
                test_read_user_details(conn, user['user_id'])
            
            # 6. Test UPDATE
            for user in created_users:
                test_update_user(conn, user['user_id'], user['role'])
            
            # 7. Test DEACTIVATE
            for user in created_users:
                test_deactivate_user(conn, user['user_id'])
            
            # Clean up
            cleanup_test_users(conn, created_users)
        
        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)
        
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
