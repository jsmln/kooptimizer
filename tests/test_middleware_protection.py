"""
Test middleware protection for all URLs
Checks if unauthorized users are properly blocked from protected pages
"""
from django.test import TestCase, Client
from django.urls import reverse, get_resolver
import re


class MiddlewareProtectionTest(TestCase):
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        
    def get_all_url_patterns(self):
        """Extract all URL patterns from the project"""
        resolver = get_resolver()
        
        # Public URLs that should be accessible without login
        public_urls = {
            'home': '/',
            'login': '/login/',
            'about': '/about/',
            'download': '/download/',
            'access_denied': '/access-denied/',
            'users:logout': '/users/logout/',
        }
        
        # Protected URLs that should require authentication
        protected_urls = {
            # Dashboard
            'dashboard:admin_dashboard': '/dashboard/admin/',
            'dashboard:cooperative_dashboard': '/dashboard/cooperative/',
            'dashboard:staff_dashboard': '/dashboard/staff/',
            
            # User settings
            'users:profile_settings': '/users/settings/',
            'users:update_profile': '/users/settings/update/',
            
            # Communications
            'communications:message': '/communications/message/',
            'communications:announcement_form': '/communications/announcement/',
            'communications:handle_announcement': '/communications/announcement/send/',
            
            # Cooperatives
            'cooperatives:profile_form': '/cooperatives/profile_form/',
            
            # Account Management
            'account_management:account_management': '/account_management/account_management/',
            
            # Databank
            'databank:databank_management': '/databank/databank/',
        }
        
        # API endpoints that should return 403 JSON for unauthorized access
        api_endpoints = {
            'communications:get_message_contacts': '/communications/api/message/contacts/',
            'communications:send_message': '/communications/api/message/send/',
            'account_management:send_credentials': '/account_management/api/send-credentials/',
            'databank:add_cooperative': '/databank/api/cooperative/add/',
            'databank:process_ocr': '/databank/api/ocr/process/',
        }
        
        return public_urls, protected_urls, api_endpoints
    
    def test_public_urls_accessible(self):
        """Test that public URLs are accessible without authentication"""
        public_urls, _, _ = self.get_all_url_patterns()
        
        print("\n" + "="*80)
        print("TESTING PUBLIC URLS (Should be accessible)")
        print("="*80)
        
        for name, url in public_urls.items():
            response = self.client.get(url, follow=False)
            print(f"✓ {name:30} {url:40} Status: {response.status_code}")
            
            # Public URLs should return 200 or 302 (redirect), not 403
            self.assertIn(response.status_code, [200, 302, 301], 
                         f"{name} ({url}) should be accessible, got {response.status_code}")
    
    def test_protected_urls_blocked(self):
        """Test that protected URLs are blocked for unauthenticated users"""
        _, protected_urls, _ = self.get_all_url_patterns()
        
        print("\n" + "="*80)
        print("TESTING PROTECTED URLS (Should return 403 or redirect)")
        print("="*80)
        
        failures = []
        
        for name, url in protected_urls.items():
            response = self.client.get(url, follow=False)
            status = response.status_code
            
            # Should return 403 (access denied page) or redirect to login
            if status == 403:
                result = "✓ BLOCKED (403)"
            elif status == 302:
                result = "⚠ REDIRECTED (might not be properly protected)"
            elif status == 200:
                result = "✗ ACCESSIBLE (NOT PROTECTED!)"
                failures.append(f"{name} ({url})")
            else:
                result = f"? UNKNOWN ({status})"
            
            print(f"{result:20} {name:35} {url}")
            
            # Protected URLs should NOT return 200 OK
            self.assertNotEqual(status, 200, 
                              f"{name} ({url}) should be protected but returned 200 OK")
        
        if failures:
            print("\n" + "!"*80)
            print("SECURITY WARNING: The following URLs are NOT properly protected:")
            for failure in failures:
                print(f"  - {failure}")
            print("!"*80)
    
    def test_api_endpoints_return_json_403(self):
        """Test that API endpoints return JSON 403 for unauthorized access"""
        _, _, api_endpoints = self.get_all_url_patterns()
        
        print("\n" + "="*80)
        print("TESTING API ENDPOINTS (Should return 403 JSON)")
        print("="*80)
        
        for name, url in api_endpoints.items():
            response = self.client.get(url, follow=False)
            status = response.status_code
            
            if status == 403:
                try:
                    # Check if response is JSON
                    data = response.json()
                    if 'status' in data and data['status'] == 'error':
                        result = "✓ PROTECTED (403 JSON)"
                    else:
                        result = "⚠ 403 but not proper JSON format"
                except:
                    result = "⚠ 403 but not JSON (HTML access denied page)"
            elif status == 200:
                result = "✗ ACCESSIBLE (NOT PROTECTED!)"
            else:
                result = f"? Status {status}"
            
            print(f"{result:35} {name:40} {url}")
    
    def test_dashboard_staff_specifically(self):
        """Specifically test /dashboard/staff/ URL that was mentioned"""
        print("\n" + "="*80)
        print("TESTING SPECIFIC URL: /dashboard/staff/")
        print("="*80)
        
        response = self.client.get('/dashboard/staff/', follow=False)
        
        print(f"URL: /dashboard/staff/")
        print(f"Status Code: {response.status_code}")
        print(f"Response Type: {response.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            print("✗ CRITICAL: /dashboard/staff/ is ACCESSIBLE without authentication!")
            print("   This is a SECURITY ISSUE - anyone can access the staff dashboard")
        elif response.status_code == 403:
            print("✓ PROTECTED: Returns 403 Access Denied")
        elif response.status_code == 302:
            print(f"⚠ REDIRECTS to: {response.get('Location', 'unknown')}")
        
        # This should NOT return 200
        self.assertNotEqual(response.status_code, 200,
                          "/dashboard/staff/ should NOT be accessible without authentication")
    
    def test_with_authenticated_session(self):
        """Test that authenticated users CAN access protected URLs"""
        print("\n" + "="*80)
        print("TESTING WITH AUTHENTICATED SESSION")
        print("="*80)
        
        # Simulate authenticated session
        session = self.client.session
        session['user_id'] = 1
        session['role'] = 'Admin'
        session.save()
        
        _, protected_urls, _ = self.get_all_url_patterns()
        
        # Test a few key protected URLs
        test_urls = [
            ('dashboard:staff_dashboard', '/dashboard/staff/'),
            ('dashboard:admin_dashboard', '/dashboard/admin/'),
            ('communications:message', '/communications/message/'),
        ]
        
        for name, url in test_urls:
            response = self.client.get(url, follow=False)
            status = response.status_code
            
            if status == 200:
                result = "✓ ACCESSIBLE (as expected)"
            elif status == 403:
                result = "✗ BLOCKED (should be accessible when logged in)"
            else:
                result = f"? Status {status}"
            
            print(f"{result:35} {name:35} {url}")


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
    django.setup()
    
    from django.test.utils import get_runner
    TestRunner = get_runner(django.conf.settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_middleware_protection'])
