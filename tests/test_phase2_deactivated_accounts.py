"""
Test Phase 2 Implementation:
1. Test filter parameter in sp_get_all_user_accounts
2. Verify Django view handles filter correctly
3. Check deactivated accounts display
"""
import requests

BASE_URL = 'http://127.0.0.1:8000'

# Test session (you'll need to be logged in)
session = requests.Session()

print("=" * 80)
print("PHASE 2 IMPLEMENTATION TEST")
print("=" * 80)

# Test 1: Load account management with default filter (active)
print("\n1. Testing default filter (active accounts):")
response = session.get(f'{BASE_URL}/account_management/account_management/')
if response.status_code == 200:
    print(f"   ✓ Status: {response.status_code}")
    if 'deactivated' in response.text.lower():
        print("   ✓ Deactivated tab found in HTML")
    else:
        print("   ✗ Deactivated tab NOT found in HTML")
else:
    print(f"   ✗ Status: {response.status_code}")

# Test 2: Load with deactivated filter
print("\n2. Testing deactivated filter:")
response = session.get(f'{BASE_URL}/account_management/account_management/?filter=deactivated')
if response.status_code == 200:
    print(f"   ✓ Status: {response.status_code}")
    if 'current_filter' in response.text:
        print("   ✓ Filter parameter processed")
else:
    print(f"   ✗ Status: {response.status_code}")

# Test 3: Load with all filter
print("\n3. Testing all accounts filter:")
response = session.get(f'{BASE_URL}/account_management/account_management/?filter=all')
if response.status_code == 200:
    print(f"   ✓ Status: {response.status_code}")
else:
    print(f"   ✗ Status: {response.status_code}")

print("\n" + "=" * 80)
print("Note: You need to be logged in to fully test this functionality")
print("Please visit the page in your browser and verify:")
print("  1. Deactivated tab appears (Admin only)")
print("  2. Clicking Deactivated tab shows deactivated accounts")
print("  3. Reactivate button appears for selected deactivated accounts")
print("  4. Clicking Reactivate restores the account")
print("=" * 80)
