"""
Quick test to verify all key endpoints are accessible after folder reorganization.
Tests that URLs resolve correctly and pages load without import errors.
"""

import requests
import time

def test_endpoints():
    """Test key endpoints to verify they load correctly"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Endpoints to test (public pages that don't require authentication)
    # Note: Access Denied page intentionally returns 403
    endpoints = {
        "Home Page": ("/", [200, 302]),
        "Login Page": ("/login/", [200, 302]),
        "About Page": ("/about/", [200, 302]),
        "Download Page": ("/download/", [200, 302]),
        "Access Denied Page": ("/access-denied/", [403]),  # Intentionally returns 403
    }
    
    print("\n" + "="*70)
    print("  ENDPOINT ACCESSIBILITY TEST")
    print("="*70)
    print("  Testing if pages load correctly after folder reorganization\n")
    
    passed = 0
    failed = 0
    
    for name, (endpoint, expected_codes) in endpoints.items():
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            
            # Check if we got an expected response code
            if response.status_code in expected_codes:
                print(f"✅ {name:.<40} OK (Status: {response.status_code})")
                passed += 1
            else:
                print(f"❌ {name:.<40} FAIL (Status: {response.status_code}, Expected: {expected_codes})")
                failed += 1
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {name:.<40} FAIL (Server not running)")
            failed += 1
        except requests.exceptions.Timeout:
            print(f"❌ {name:.<40} FAIL (Timeout)")
            failed += 1
        except Exception as e:
            print(f"❌ {name:.<40} FAIL ({str(e)})")
            failed += 1
    
    print("\n" + "="*70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("✅ All endpoints are accessible!")
        print("✅ Folder reorganization did not break URL routing")
        return True
    else:
        print("⚠️  Some endpoints failed. Check the server logs.")
        return False

if __name__ == "__main__":
    print("Waiting for server to be ready...")
    time.sleep(2)  # Give server time to start
    
    success = test_endpoints()
    exit(0 if success else 1)
