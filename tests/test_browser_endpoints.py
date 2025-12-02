"""
Quick browser test - make a test request to verify the fix works
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_update_user():
    """Test update user endpoint"""
    print("\n" + "="*80)
    print("TESTING UPDATE USER ENDPOINT")
    print("="*80)
    
    # First get user details
    user_id = 1
    response = requests.get(f"{BASE_URL}/account_management/api/get-user-details/{user_id}/")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✓ Got user details for user {user_id}")
        print(f"  Current: {user_data['details']}")
        
        # Now try to update
        update_data = {
            'name': user_data['details']['fullname'],
            'email': user_data['details']['email'],
            'contact': user_data['details']['mobile_number'],
            'gender': user_data['details']['gender'],
            'position': user_data['details']['position'],
            'type': user_data['details']['role']
        }
        
        print(f"\nAttempting update...")
        response = requests.post(
            f"{BASE_URL}/account_management/api/update-user/{user_id}/",
            json=update_data
        )
        
        if response.status_code == 200:
            print(f"✓ UPDATE SUCCESS: {response.json()}")
            return True
        else:
            print(f"✗ UPDATE FAILED: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    else:
        print(f"✗ Failed to get user details: {response.status_code}")
        return False

def test_get_user():
    """Test get user endpoint"""
    print("\n" + "="*80)
    print("TESTING GET USER ENDPOINT")
    print("="*80)
    
    user_id = 5
    response = requests.get(f"{BASE_URL}/account_management/api/get-user-details/{user_id}/")
    
    if response.status_code == 200:
        print(f"✓ GET SUCCESS for user {user_id}")
        print(f"  Details: {response.json()['details']}")
        return True
    else:
        print(f"✗ GET FAILED: {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("BROWSER ENDPOINT TEST")
    print("Make sure Django server is running at http://127.0.0.1:8000")
    print("="*80)
    
    try:
        # Test GET
        get_result = test_get_user()
        
        # Test UPDATE
        update_result = test_update_user()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"GET: {'✓ PASS' if get_result else '✗ FAIL'}")
        print(f"UPDATE: {'✓ PASS' if update_result else '✗ FAIL'}")
        
        if get_result and update_result:
            print("\n✓ ALL ENDPOINTS WORKING!")
            print("The errors you saw earlier should be fixed now.")
        else:
            print("\n✗ Some endpoints failed - check server logs")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to Django server")
        print("Make sure the server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
