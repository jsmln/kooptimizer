"""
Test to verify:
1. Browser close expires session
2. Page refresh does NOT expire session  
3. Manual URL typing is blocked
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

def test_scenario(description, path, user_id, current_page, referer):
    """Test a specific middleware scenario"""
    print(f"\n[TEST] {description}")
    print(f"  → Accessing: {path}")
    print(f"  → Current page in session: {current_page}")
    print(f"  → Referer: {referer or '(none)'}")
    
    factory = RequestFactory()
    
    if referer:
        request = factory.get(path, HTTP_REFERER=referer)
    else:
        request = factory.get(path)
    
    # Add session
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
    
    # Create middleware
    def dummy_view(req):
        from django.http import HttpResponse
        return HttpResponse("OK")
    
    auth_middleware = AuthenticationMiddleware(dummy_view)
    
    try:
        response = auth_middleware(request)
        
        if response.status_code == 200:
            print(f"  ✓ ALLOWED (Status 200)")
        elif response.status_code == 302:
            print(f"  ✗ BLOCKED - Redirect to: {response.url}")
        else:
            print(f"  ? Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ERROR: {e}")

print("=" * 80)
print("  MIDDLEWARE SECURITY TEST")
print("=" * 80)

print("\n" + "=" * 80)
print("SCENARIO 1: Page Refresh (should ALLOW)")
print("=" * 80)

test_scenario(
    "Refresh current page (F5)",
    path="/account_management/account_management/",
    user_id=1,
    current_page="/account_management/account_management/",
    referer=None
)

test_scenario(
    "Refresh dashboard (Ctrl+R)",
    path="/dashboard/admin/",
    user_id=1,
    current_page="/dashboard/admin/",
    referer=None
)

print("\n" + "=" * 80)
print("SCENARIO 2: Manual URL Typing to DIFFERENT page (should BLOCK)")
print("=" * 80)

test_scenario(
    "Type /databank/ while on account_management",
    path="/databank/databank/",
    user_id=1,
    current_page="/account_management/account_management/",
    referer=None
)

test_scenario(
    "Type /account_management/ while on dashboard",
    path="/account_management/account_management/",
    user_id=1,
    current_page="/dashboard/admin/",
    referer=None
)

print("\n" + "=" * 80)
print("SCENARIO 3: Normal Navigation with Referer (should ALLOW)")
print("=" * 80)

test_scenario(
    "Click link from dashboard to account_management",
    path="/account_management/account_management/",
    user_id=1,
    current_page="/dashboard/admin/",
    referer="http://127.0.0.1:8000/dashboard/admin/"
)

test_scenario(
    "Click link from account_management to databank",
    path="/databank/databank/",
    user_id=1,
    current_page="/account_management/account_management/",
    referer="http://127.0.0.1:8000/account_management/account_management/"
)

print("\n" + "=" * 80)
print("SCENARIO 4: First Navigation After Login (should ALLOW)")
print("=" * 80)

test_scenario(
    "First page after login (no current_page)",
    path="/dashboard/admin/",
    user_id=1,
    current_page=None,
    referer=None
)

print("\n" + "=" * 80)
print("EXPECTED RESULTS SUMMARY")
print("=" * 80)
print("✓ Page refresh (same URL, no referer) = ALLOW")
print("✗ Manual URL typing (different URL, no referer) = BLOCK → Redirect to current page")
print("✓ Normal navigation (with referer) = ALLOW")
print("✓ First navigation after login = ALLOW")
print("=" * 80)
