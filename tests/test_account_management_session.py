"""
Test to identify why account management page loses session on refresh
while other pages work fine.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from apps.core.middleware import AuthenticationMiddleware
from apps.account_management.views import account_management
import json

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_test(text):
    print(f"\n[TEST] {text}")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"  → {text}")

# TEST 1: Check if account_management view modifies session
print_header("TEST 1: Does account_management view clear or modify session?")

factory = RequestFactory()
request = factory.get('/account_management/account_management/')

# Add session
session_middleware = SessionMiddleware(lambda x: None)
session_middleware.process_request(request)
request.session['user_id'] = 1
request.session['role'] = 'admin'
request.session['current_page'] = '/dashboard/admin/'
request.session.save()

print_test("Session BEFORE calling account_management view:")
print_info(f"user_id: {request.session.get('user_id')}")
print_info(f"role: {request.session.get('role')}")
print_info(f"current_page: {request.session.get('current_page')}")
print_info(f"Session key: {request.session.session_key}")

try:
    response = account_management(request)
    print_test("Session AFTER calling account_management view:")
    print_info(f"user_id: {request.session.get('user_id')}")
    print_info(f"role: {request.session.get('role')}")
    print_info(f"current_page: {request.session.get('current_page')}")
    
    if request.session.get('user_id') == 1:
        print_success("Session preserved after view execution")
    else:
        print_error("Session lost after view execution!")
        
except Exception as e:
    print_error(f"View execution failed: {e}")

# TEST 2: Check if view has any decorators that might clear session
print_header("TEST 2: Check account_management view decorators")

import inspect
from apps.account_management import views

print_test("Inspecting account_management function:")
source = inspect.getsource(views.account_management)
lines = source.split('\n')[:10]  # First 10 lines

for line in lines:
    if '@' in line or 'def account_management' in line:
        print_info(line.strip())

# TEST 3: Simulate full request cycle with middleware
print_header("TEST 3: Simulate full request with middleware stack")

client = Client()

print_test("Login first:")
login_response = client.post('/login/', {
    'username': 'admin',
    'password': 'admin123'
})
print_info(f"Login status: {login_response.status_code}")

if login_response.status_code == 302:
    print_success("Login successful")
    
    # Check session after login
    session = client.session
    print_info(f"Session user_id: {session.get('user_id')}")
    print_info(f"Session role: {session.get('role')}")
    
    print_test("\nAccess account management page:")
    response = client.get('/account_management/account_management/')
    print_info(f"Response status: {response.status_code}")
    
    # Check session after first access
    session = client.session
    print_info(f"Session user_id after first access: {session.get('user_id')}")
    print_info(f"Session current_page: {session.get('current_page')}")
    
    if session.get('user_id'):
        print_success("Session maintained on first access")
    else:
        print_error("Session lost on first access!")
    
    print_test("\nRefresh account management page (same URL):")
    response2 = client.get('/account_management/account_management/')
    print_info(f"Response status: {response2.status_code}")
    
    # Check session after refresh
    session = client.session
    print_info(f"Session user_id after refresh: {session.get('user_id')}")
    print_info(f"Session current_page: {session.get('current_page')}")
    
    if response2.status_code == 200:
        print_success("Refresh successful - no redirect to login")
    elif response2.status_code == 302:
        print_error(f"Refresh caused redirect to: {response2.url}")
    else:
        print_error(f"Unexpected status code: {response2.status_code}")
        
else:
    print_error("Login failed - check credentials")

# TEST 4: Compare with other pages
print_header("TEST 4: Compare account_management with other pages")

client2 = Client()
client2.post('/login/', {'username': 'admin', 'password': 'admin123'})

pages_to_test = [
    ('/dashboard/admin/', 'Admin Dashboard'),
    ('/databank/databank/', 'Databank'),
    ('/account_management/account_management/', 'Account Management'),
]

for url, name in pages_to_test:
    print_test(f"Testing: {name}")
    
    # First access
    r1 = client2.get(url)
    print_info(f"First access: {r1.status_code}")
    session1 = client2.session
    user_id_1 = session1.get('user_id')
    
    # Refresh (second access)
    r2 = client2.get(url)
    print_info(f"Refresh: {r2.status_code}")
    session2 = client2.session
    user_id_2 = session2.get('user_id')
    
    if r2.status_code == 200 and user_id_2:
        print_success(f"{name}: Refresh works ✓")
    else:
        print_error(f"{name}: Refresh FAILED - Status: {r2.status_code}, Session: {user_id_2}")

# TEST 5: Check URL routing configuration
print_header("TEST 5: Check account_management URL configuration")

from django.urls import resolve
try:
    resolved = resolve('/account_management/account_management/')
    print_info(f"URL name: {resolved.url_name}")
    print_info(f"App namespace: {resolved.namespace}")
    print_info(f"View function: {resolved.func}")
    print_info(f"Full URL name: {resolved.namespace}:{resolved.url_name}" if resolved.namespace else resolved.url_name)
except Exception as e:
    print_error(f"URL resolution failed: {e}")

# TEST 6: Check if there's a csrf_exempt decorator
print_header("TEST 6: Check for CSRF exempt or other decorators")

print_test("Checking account_management view attributes:")
view_func = views.account_management

attrs_to_check = [
    'csrf_exempt',
    'csrf_protect', 
    'ensure_csrf_cookie',
    'login_required',
    '__name__',
    '__wrapped__'
]

for attr in attrs_to_check:
    if hasattr(view_func, attr):
        print_info(f"{attr}: {getattr(view_func, attr)}")
    else:
        print_info(f"{attr}: Not present")

print("\n" + "=" * 80)
print("  TEST SUITE COMPLETE")
print("=" * 80)
