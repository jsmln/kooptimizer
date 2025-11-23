"""
Test middleware behavior specifically for account_management page
"""
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware  
from apps.core.middleware import AuthenticationMiddleware

def create_request_with_session(path, user_id=None, current_page=None, referer=None):
    """Helper to create a request with session"""
    factory = RequestFactory()
    
    # Create request with or without referer
    if referer:
        request = factory.get(path, HTTP_REFERER=referer)
    else:
        request = factory.get(path)
    
    # Add session middleware
    session_middleware = SessionMiddleware(lambda x: None)
    session_middleware.process_request(request)
    
    if user_id:
        request.session['user_id'] = user_id
        request.session['role'] = 'admin'
    
    if current_page:
        request.session['current_page'] = current_page
        
    request.session.save()
    
    # Add message middleware
    msg_middleware = MessageMiddleware(lambda x: None)
    msg_middleware.process_request(request)
    
    return request

def test_middleware(description, path, user_id=None, current_page=None, referer=None):
    """Test middleware with specific conditions"""
    print(f"\n[TEST] {description}")
    print(f"  Path: {path}")
    print(f"  user_id in session: {user_id}")
    print(f"  current_page in session: {current_page}")
    print(f"  HTTP_REFERER: {referer or '(none)'}")
    
    request = create_request_with_session(path, user_id, current_page, referer)
    
    # Create middleware
    def dummy_view(req):
        from django.http import HttpResponse
        return HttpResponse("OK")
    
    auth_middleware = AuthenticationMiddleware(dummy_view)
    
    try:
        response = auth_middleware(request)
        
        if hasattr(response, 'status_code'):
            print(f"  → Result: Status {response.status_code}")
            
            if response.status_code == 302:
                print(f"  → Redirect to: {response.url}")
            elif response.status_code == 200:
                print(f"  → ✓ Request allowed")
        else:
            print(f"  → Result type: {type(response)}")
            
    except Exception as e:
        print(f"  → Error: {e}")

print("=" * 80)
print("  MIDDLEWARE BEHAVIOR TEST")
print("=" * 80)

# TEST 1: First visit to account_management (after login, coming from dashboard)
test_middleware(
    "First visit from dashboard (with referer)",
    path="/account_management/account_management/",
    user_id=1,
    current_page="/dashboard/admin/",
    referer="http://127.0.0.1:8000/dashboard/admin/"
)

# TEST 2: Refresh account_management (F5 - no referer)
test_middleware(
    "Refresh account_management (F5 - no referer)",
    path="/account_management/account_management/",
    user_id=1,
    current_page="/account_management/account_management/",
    referer=None
)

# TEST 3: Hard refresh with Ctrl+Shift+R (no referer, possibly no session)
test_middleware(
    "Hard refresh - session LOST (simulating browser behavior)",
    path="/account_management/account_management/",
    user_id=None,  # Session cleared
    current_page="/account_management/account_management/",  # But current_page might still be there
    referer=None
)

# TEST 4: Compare with dashboard refresh
test_middleware(
    "Refresh dashboard (F5 - no referer)",
    path="/dashboard/admin/",
    user_id=1,
    current_page="/dashboard/admin/",
    referer=None
)

# TEST 5: Dashboard hard refresh with lost session
test_middleware(
    "Dashboard hard refresh - session LOST",
    path="/dashboard/admin/",
    user_id=None,
    current_page="/dashboard/admin/",
    referer=None
)

# TEST 6: Type different URL manually (with session)
test_middleware(
    "Manually type different URL (with session)",
    path="/databank/databank/",
    user_id=1,
    current_page="/account_management/account_management/",
    referer=None
)

print("\n" + "=" * 80)
print("  KEY FINDINGS:")
print("=" * 80)
print("If account_management redirects to login but dashboard doesn't,")
print("then the issue is likely:")
print("  1. Browser clearing cookies specifically for this page")
print("  2. Special character in URL causing session cookie mismatch")
print("  3. CSRF cookie handling difference with @ensure_csrf_cookie")
print("=" * 80)
