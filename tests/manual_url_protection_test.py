"""
Manual test script to check URL protection
Run this with: python tests/manual_url_protection_test.py
"""
import requests
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Base URL - adjust if needed
BASE_URL = "http://127.0.0.1:8000"

# Define URL categories
PUBLIC_URLS = {
    'Home': '/',
    'Login': '/login/',
    'About': '/about/',
    'Download': '/download/',
    'Access Denied': '/access-denied/',
}

PROTECTED_URLS = {
    'Admin Dashboard': '/dashboard/admin/',
    'Cooperative Dashboard': '/dashboard/cooperative/',
    'Staff Dashboard': '/dashboard/staff/',
    'Profile Settings': '/users/settings/',
    'Messages': '/communications/message/',
    'Announcements': '/communications/announcement/',
    'Cooperative Profile': '/cooperatives/profile_form/',
    'Account Management': '/account_management/account_management/',
    'Databank': '/databank/databank/',
}

API_ENDPOINTS = {
    'Get Message Contacts': '/communications/api/message/contacts/',
    'Send Message': '/communications/api/message/send/',
    'Send Credentials': '/account_management/api/send-credentials/',
    'Add Cooperative': '/databank/api/cooperative/add/',
}


def test_url(name, url, session=None):
    """Test a single URL and return results"""
    try:
        if session:
            response = session.get(BASE_URL + url, allow_redirects=False)
        else:
            response = requests.get(BASE_URL + url, allow_redirects=False)
        
        status = response.status_code
        content_type = response.headers.get('Content-Type', '')
        
        return {
            'status': status,
            'content_type': content_type,
            'is_json': 'application/json' in content_type,
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def print_test_result(name, url, result, expected_protected=False):
    """Print formatted test result"""
    status = result.get('status')
    
    if status == 'ERROR':
        print(f"{Fore.YELLOW}⚠ ERROR: {name:35} {url:40}")
        print(f"  {result.get('error')}")
        return False
    
    # For public URLs
    if not expected_protected:
        if status in [200, 302]:
            print(f"{Fore.GREEN}✓ PUBLIC: {name:35} {url:40} Status: {status}")
            return True
        else:
            print(f"{Fore.RED}✗ BLOCKED: {name:35} {url:40} Status: {status} (Should be accessible!)")
            return False
    
    # For protected URLs
    else:
        if status == 200:
            print(f"{Fore.RED}✗ EXPOSED: {name:35} {url:40} Status: {status} (NOT PROTECTED!)")
            return False
        elif status == 403:
            if result.get('is_json'):
                print(f"{Fore.GREEN}✓ PROTECTED (JSON): {name:35} {url:40} Status: {status}")
            else:
                print(f"{Fore.GREEN}✓ PROTECTED (HTML): {name:35} {url:40} Status: {status}")
            return True
        elif status == 302:
            print(f"{Fore.YELLOW}⚠ REDIRECT: {name:35} {url:40} Status: {status}")
            return True
        else:
            print(f"{Fore.YELLOW}? UNKNOWN: {name:35} {url:40} Status: {status}")
            return True


def main():
    print(f"\n{Style.BRIGHT}{'='*100}")
    print(f"{Style.BRIGHT}KOOPTIMIZER URL PROTECTION TEST")
    print(f"{Style.BRIGHT}Testing against: {BASE_URL}")
    print(f"{Style.BRIGHT}{'='*100}\n")
    
    # Test 1: Public URLs (should be accessible)
    print(f"\n{Style.BRIGHT}{Fore.CYAN}TEST 1: PUBLIC URLS (Should be accessible without login)")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'-'*100}")
    public_results = []
    for name, url in PUBLIC_URLS.items():
        result = test_url(name, url)
        passed = print_test_result(name, url, result, expected_protected=False)
        public_results.append(passed)
    
    # Test 2: Protected URLs without authentication
    print(f"\n{Style.BRIGHT}{Fore.CYAN}TEST 2: PROTECTED URLS (Should be blocked without login)")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'-'*100}")
    protected_results = []
    for name, url in PROTECTED_URLS.items():
        result = test_url(name, url)
        passed = print_test_result(name, url, result, expected_protected=True)
        protected_results.append(passed)
    
    # Test 3: API Endpoints without authentication
    print(f"\n{Style.BRIGHT}{Fore.CYAN}TEST 3: API ENDPOINTS (Should return 403 JSON without login)")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'-'*100}")
    api_results = []
    for name, url in API_ENDPOINTS.items():
        result = test_url(name, url)
        passed = print_test_result(name, url, result, expected_protected=True)
        api_results.append(passed)
    
    # Test 4: Specific URL mentioned by user
    print(f"\n{Style.BRIGHT}{Fore.CYAN}TEST 4: SPECIFIC URL /dashboard/staff/ (User mentioned this)")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'-'*100}")
    staff_result = test_url('Staff Dashboard', '/dashboard/staff/')
    staff_passed = print_test_result('Staff Dashboard', '/dashboard/staff/', staff_result, expected_protected=True)
    
    # Summary
    print(f"\n{Style.BRIGHT}{'='*100}")
    print(f"{Style.BRIGHT}SUMMARY")
    print(f"{Style.BRIGHT}{'='*100}")
    
    public_passed = sum(public_results)
    public_total = len(public_results)
    print(f"Public URLs:     {public_passed}/{public_total} passed")
    
    protected_passed = sum(protected_results)
    protected_total = len(protected_results)
    print(f"Protected URLs:  {protected_passed}/{protected_total} passed")
    
    api_passed = sum(api_results)
    api_total = len(api_results)
    print(f"API Endpoints:   {api_passed}/{api_total} passed")
    
    print(f"\n/dashboard/staff/ specifically: {'PROTECTED ✓' if staff_passed else 'EXPOSED ✗'}")
    
    # Security warnings
    if protected_passed < protected_total or not staff_passed:
        print(f"\n{Fore.RED}{Style.BRIGHT}{'!'*100}")
        print(f"{Fore.RED}{Style.BRIGHT}⚠ SECURITY WARNING: Some protected URLs are accessible without authentication!")
        print(f"{Fore.RED}{Style.BRIGHT}{'!'*100}")
        return False
    else:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*100}")
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ ALL TESTS PASSED - URLs are properly protected")
        print(f"{Fore.GREEN}{Style.BRIGHT}{'='*100}")
        return True


if __name__ == '__main__':
    import sys
    
    print(f"\n{Fore.YELLOW}Make sure the Django development server is running at {BASE_URL}")
    print(f"{Fore.YELLOW}Run: python manage.py runserver\n")
    
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error running tests: {e}")
        sys.exit(1)
