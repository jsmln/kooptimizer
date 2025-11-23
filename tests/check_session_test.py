"""
Test to check if there's an active session allowing access
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

print("\n" + "="*80)
print("CHECKING SESSION STATUS")
print("="*80 + "\n")

# Test 1: Without session (fresh request)
print("Test 1: Fresh request (no cookies/session)")
print("-" * 80)
response = requests.get(f"{BASE_URL}/dashboard/staff/", allow_redirects=False)
print(f"URL: /dashboard/staff/")
print(f"Status Code: {response.status_code}")
print(f"Expected: 403 (Access Denied)")
print(f"Result: {'✓ PROTECTED' if response.status_code == 403 else '✗ ACCESSIBLE'}")

# Test 2: Check if response has session cookie
print("\n\nTest 2: Checking for session cookies in response")
print("-" * 80)
cookies = response.cookies
if cookies:
    print(f"Cookies received: {dict(cookies)}")
else:
    print("No cookies received")

# Test 3: Try with browser simulation
print("\n\nTest 3: Browser simulation with user-agent")
print("-" * 80)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
response = requests.get(f"{BASE_URL}/dashboard/staff/", headers=headers, allow_redirects=False)
print(f"Status Code: {response.status_code}")
print(f"Result: {'✓ PROTECTED' if response.status_code == 403 else '✗ ACCESSIBLE'}")

# Test 4: Check content of 403 response
print("\n\nTest 4: Checking 403 response content")
print("-" * 80)
if response.status_code == 403:
    if 'access denied' in response.text.lower() or 'unauthorized' in response.text.lower():
        print("✓ Shows proper access denied page")
    else:
        print("⚠ Returns 403 but might not show access denied page")
        print(f"Content preview: {response.text[:200]}...")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nIf you can open /dashboard/staff/ in your BROWSER but this test shows 403,")
print("it means you have an ACTIVE SESSION in your browser (you're logged in).")
print("\nTo verify middleware protection:")
print("1. Open a NEW INCOGNITO/PRIVATE browser window")
print("2. Go to: http://127.0.0.1:8000/dashboard/staff/")
print("3. You should see 'Access Denied' page")
print("\nOR clear your browser cookies/session and try again.")
print("="*80 + "\n")
