"""
Test the Django views for account_management CRUD operations
This simulates HTTP requests to test update and deactivate functionality
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, r'C:\Users\Noe Gonzales\Downloads\System\Kooptimizer')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory
from apps.account_management.views import update_user_view, deactivate_user_view, get_user_details_view
from django.db import connection
import json

def create_test_user():
    """Create a test user for testing"""
    print("\n" + "="*80)
    print("CREATING TEST USER")
    print("="*80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sp_create_user_profile(
                %s::varchar,
                %s::varchar,
                %s::user_role_enum,
                %s::varchar,
                %s::varchar,
                %s::varchar,
                %s::gender_enum,
                %s::varchar,
                %s::integer,
                %s::integer[]
            )
        """, [
            'test_view_user@test.com',
            'hashed_password',
            'admin',
            'Test View User',
            'test_view_user@test.com',
            '09123456789',
            'male',
            'Test Position',
            None,
            None
        ])
        result = cursor.fetchone()
        user_id = result[0]
        print(f"✓ Created test user with ID: {user_id}")
        return user_id

def test_get_user_details(user_id):
    """Test GET user details view"""
    print("\n" + "="*80)
    print(f"TESTING GET USER DETAILS - User ID: {user_id}")
    print("="*80)
    
    factory = RequestFactory()
    request = factory.get(f'/api/get-user-details/{user_id}/')
    
    try:
        response = get_user_details_view(request, user_id)
        response_data = json.loads(response.content)
        
        if response.status_code == 200 and response_data['status'] == 'success':
            print("✓ GET user details PASSED")
            print(f"  User details: {json.dumps(response_data['details'], indent=2)}")
            return True
        else:
            print(f"✗ GET user details FAILED: {response_data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ GET user details ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_user(user_id):
    """Test UPDATE user view"""
    print("\n" + "="*80)
    print(f"TESTING UPDATE USER - User ID: {user_id}")
    print("="*80)
    
    factory = RequestFactory()
    update_data = {
        'name': 'Updated Test User',
        'email': 'updated_test@test.com',
        'contact': '09987654321',
        'gender': 'female',
        'position': 'Updated Position',
        'type': 'admin'
    }
    
    request = factory.post(
        f'/api/update-user/{user_id}/',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    try:
        response = update_user_view(request, user_id)
        response_data = json.loads(response.content)
        
        if response.status_code == 200 and response_data['status'] == 'success':
            print("✓ UPDATE user PASSED")
            print(f"  Message: {response_data['message']}")
            
            # Verify the update
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_get_user_details(%s)", [user_id])
                details = cursor.fetchone()[0]
                print(f"  Verified update: {json.dumps(details, indent=2)}")
            
            return True
        else:
            print(f"✗ UPDATE user FAILED: {response_data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ UPDATE user ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deactivate_user(user_id):
    """Test DEACTIVATE user view"""
    print("\n" + "="*80)
    print(f"TESTING DEACTIVATE USER - User ID: {user_id}")
    print("="*80)
    
    factory = RequestFactory()
    request = factory.post(f'/api/deactivate-user/{user_id}/')
    
    try:
        # Check status before
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_active FROM users WHERE user_id = %s", [user_id])
            before = cursor.fetchone()[0]
            print(f"  Before: is_active = {before}")
        
        response = deactivate_user_view(request, user_id)
        response_data = json.loads(response.content)
        
        if response.status_code == 200 and response_data['status'] == 'success':
            # Check status after
            with connection.cursor() as cursor:
                cursor.execute("SELECT is_active FROM users WHERE user_id = %s", [user_id])
                after = cursor.fetchone()[0]
                print(f"  After: is_active = {after}")
            
            if not after:
                print("✓ DEACTIVATE user PASSED")
                print(f"  Message: {response_data['message']}")
                return True
            else:
                print("✗ DEACTIVATE user FAILED: User still active")
                return False
        else:
            print(f"✗ DEACTIVATE user FAILED: {response_data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ DEACTIVATE user ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_user(user_id):
    """Clean up test user"""
    print("\n" + "="*80)
    print("CLEANING UP TEST USER")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM admin WHERE user_id = %s", [user_id])
            cursor.execute("DELETE FROM users WHERE user_id = %s", [user_id])
        print(f"✓ Cleaned up test user (user_id: {user_id})")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

def main():
    """Run all view tests"""
    print("\n" + "="*80)
    print("DJANGO VIEWS TEST - Account Management CRUD")
    print("="*80)
    
    # Create test user
    user_id = create_test_user()
    
    try:
        # Test all operations
        results = {
            'GET': test_get_user_details(user_id),
            'UPDATE': test_update_user(user_id),
            'DEACTIVATE': test_deactivate_user(user_id)
        }
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        for operation, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{operation}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            print("\n✓ ALL TESTS PASSED - Django views are working correctly!")
        else:
            print("\n✗ SOME TESTS FAILED - Check errors above")
        
    finally:
        # Cleanup
        cleanup_test_user(user_id)
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)

if __name__ == "__main__":
    main()
