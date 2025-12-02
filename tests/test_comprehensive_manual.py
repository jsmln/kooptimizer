"""
Comprehensive Manual Test Script for Kooptimizer
Tests all functionalities per page and per role
Detects duplication issues
"""

import os
import sys
import django
from pathlib import Path
import ast
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import Client, RequestFactory
from django.urls import reverse
from apps.users.models import User
try:
    from apps.communications.models import Announcement
except ImportError:
    Announcement = None
try:
    from apps.cooperatives.models import Cooperative
except ImportError:
    Cooperative = None


class ComprehensiveTester:
    """Comprehensive testing for all pages and roles"""
    
    def __init__(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80 + "\n")
    
    def test_duplication_issues(self):
        """Test for duplication issues in codebase"""
        self.print_header("DUPLICATION DETECTION")
        
        project_root = Path(__file__).parent
        duplications = defaultdict(list)
        
        # 1. Check for duplicate decorators
        print("[1] Checking for duplicate decorators...")
        decorator_files = defaultdict(list)
        
        for py_file in project_root.rglob('apps/**/*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'def login_required' in content:
                        decorator_files['login_required'].append(str(py_file))
                    if 'def role_required' in content:
                        decorator_files['role_required'].append(str(py_file))
                    if 'def custom_login_required' in content:
                        decorator_files['custom_login_required'].append(str(py_file))
            except:
                pass
        
        for decorator, files in decorator_files.items():
            if len(files) > 1:
                print(f"    [!] WARNING: '{decorator}' found in {len(files)} files:")
                for f in files:
                    print(f"        - {f}")
                self.results['warnings'].append({
                    'type': 'Duplicate Decorator',
                    'name': decorator,
                    'locations': files
                })
            else:
                print(f"    [OK] '{decorator}' is unique")
        
        # 2. Check for duplicate models
        print("\n[2] Checking for duplicate models...")
        model_files = defaultdict(list)
        
        for py_file in project_root.rglob('apps/**/models.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check if it's a model (has Meta or models.Model)
                            for base in node.bases:
                                if isinstance(base, ast.Attribute):
                                    if base.attr == 'Model':
                                        model_files[node.name].append(str(py_file))
            except:
                pass
        
        for model, files in model_files.items():
            if len(files) > 1:
                print(f"    [!] WARNING: Model '{model}' found in {len(files)} files:")
                for f in files:
                    print(f"        - {f}")
                self.results['warnings'].append({
                    'type': 'Duplicate Model',
                    'name': model,
                    'locations': files
                })
        
        # 3. Check for duplicate stored procedures
        print("\n[3] Checking for duplicate stored procedures...")
        sp_files = list(project_root.glob('stored_procedures/*.sql'))
        sp_names = defaultdict(list)
        
        for sp_file in sp_files:
            try:
                with open(sp_file, 'r', encoding='utf-8') as f:
                    content = f.read().upper()
                    # Extract procedure names
                    import re
                    matches = re.findall(r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|FUNCTION)\s+(\w+)', content)
                    for match in matches:
                        sp_names[match].append(sp_file.name)
            except:
                pass
        
        for sp_name, files in sp_names.items():
            if len(files) > 1:
                print(f"    [!] WARNING: Stored procedure '{sp_name}' found in {len(files)} files:")
                for f in files:
                    print(f"        - {f}")
                self.results['warnings'].append({
                    'type': 'Duplicate Stored Procedure',
                    'name': sp_name,
                    'locations': files
                })
        
        # 4. Check for duplicate signal handlers
        print("\n[4] Checking for duplicate signal handlers...")
        signal_files = defaultdict(list)
        
        for py_file in project_root.rglob('apps/**/signals.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '@receiver' in content:
                        signal_files['signal_handlers'].append(str(py_file))
            except:
                pass
        
        if signal_files['signal_handlers']:
            print(f"    [INFO] Found signal handlers in {len(signal_files['signal_handlers'])} files")
            for f in signal_files['signal_handlers']:
                print(f"        - {f}")
        
        # 5. Check for duplicate views
        print("\n[5] Checking for duplicate view functions...")
        view_funcs = defaultdict(list)
        
        for py_file in project_root.rglob('apps/**/views.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            view_funcs[node.name].append(str(py_file))
            except:
                pass
        
        duplicate_views = {k: v for k, v in view_funcs.items() if len(v) > 1}
        if duplicate_views:
            print(f"    [!] WARNING: Found {len(duplicate_views)} duplicate view function names:")
            for view_name, files in list(duplicate_views.items())[:10]:  # Show first 10
                print(f"        '{view_name}' in {len(files)} files")
                self.results['warnings'].append({
                    'type': 'Duplicate View Function',
                    'name': view_name,
                    'count': len(files)
                })
        else:
            print("    [OK] No duplicate view functions found")
    
    def test_all_roles_pages(self):
        """Test all pages for all roles"""
        self.print_header("ROLE-BASED PAGE ACCESS TESTING")
        
        roles = ['admin', 'manager', 'staff']
        
        # Define pages per app
        pages = {
            'dashboard': [
                '/dashboard/admin/',
                '/dashboard/manager/',
                '/dashboard/staff/',
            ],
            'users': [
                '/users/profile/',
                '/users/settings/',
            ],
            'account_management': [
                '/account_management/account_management/',
                '/account_management/api/users/',
            ],
            'communications': [
                '/communications/announcements/',
                '/communications/api/announcements/',
            ],
            'cooperatives': [
                '/cooperatives/list/',
                '/cooperatives/api/cooperatives/',
            ],
        }
        
        print("\nTesting page access for each role:\n")
        
        for role in roles:
            print(f"[{role.upper()}] Testing pages:")
            
            # Try to get or create a test user with this role
            try:
                users = User.objects.filter(role=role)
                if users.exists():
                    user = users.first()
                    print(f"    Using existing user: {user.username}")
                    
                    # Login
                    self.client.force_login(user)
                    
                    # Test each page
                    tested = 0
                    for app, app_pages in pages.items():
                        for page in app_pages:
                            try:
                                response = self.client.get(page)
                                status = response.status_code
                                
                                if status == 200:
                                    result = "OK"
                                    self.results['passed'].append({
                                        'role': role,
                                        'page': page,
                                        'status': status
                                    })
                                elif status in [301, 302]:
                                    result = "REDIRECT"
                                elif status == 403:
                                    result = "FORBIDDEN"
                                elif status == 404:
                                    result = "NOT FOUND"
                                else:
                                    result = f"STATUS {status}"
                                    
                                if tested < 5:  # Show first 5 for each role
                                    print(f"        {page}: {result}")
                                tested += 1
                            except Exception as e:
                                if tested < 5:
                                    print(f"        {page}: ERROR - {str(e)[:50]}")
                    
                    print(f"    Total pages tested: {tested}")
                    self.client.logout()
                else:
                    print(f"    [!] No user found with role '{role}'")
                    
            except Exception as e:
                print(f"    [!] Error testing role {role}: {str(e)[:100]}")
            
            print()
    
    def test_database_integrity(self):
        """Test database integrity and data consistency"""
        self.print_header("DATABASE INTEGRITY TESTING")
        
        print("[1] Checking User data...")
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        print(f"    Total users: {total_users}")
        print(f"    Active users: {active_users}")
        
        print("\n[2] Checking Cooperative data...")
        if Cooperative:
            coops = Cooperative.objects.count()
            print(f"    Total cooperatives: {coops}")
        else:
            print("    [!] Cooperative model not available")
        
        print("\n[3] Checking Announcements...")
        if Announcement:
            announcements = Announcement.objects.count()
            print(f"    Total announcements: {announcements}")
            
            # Check for announcements without admin or staff
            try:
                announcements_without_sender = Announcement.objects.filter(
                    admin__isnull=True, 
                    staff__isnull=True
                ).count()
                if announcements_without_sender > 0:
                    print(f"    [!] WARNING: {announcements_without_sender} announcements without sender")
                    self.results['warnings'].append({
                        'type': 'Data Integrity',
                        'issue': f'{announcements_without_sender} announcements without sender'
                    })
                else:
                    print("    [OK] All announcements have senders")
            except Exception as e:
                print(f"    [!] Could not check sender integrity: {str(e)[:100]}")
        else:
            print("    [!] Announcement model not available")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST EXECUTION SUMMARY")
        
        print(f"Total Tests Passed: {len(self.results['passed'])}")
        print(f"Total Tests Failed: {len(self.results['failed'])}")
        print(f"Total Warnings: {len(self.results['warnings'])}")
        
        if self.results['warnings']:
            print("\n" + "="*80)
            print("WARNINGS DETECTED:")
            print("="*80)
            for i, warning in enumerate(self.results['warnings'], 1):
                print(f"\n[{i}] {warning.get('type', 'Unknown')}")
                if 'name' in warning:
                    print(f"    Name: {warning['name']}")
                if 'locations' in warning:
                    print(f"    Locations: {len(warning['locations'])} files")
                if 'issue' in warning:
                    print(f"    Issue: {warning['issue']}")
        
        # Save to file
        report_path = Path(__file__).parent / 'COMPREHENSIVE_TEST_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Test Report\n\n")
            f.write(f"Generated: {Path(__file__).parent}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Tests Passed: {len(self.results['passed'])}\n")
            f.write(f"- Tests Failed: {len(self.results['failed'])}\n")
            f.write(f"- Warnings: {len(self.results['warnings'])}\n\n")
            
            if self.results['warnings']:
                f.write("## Warnings\n\n")
                for warning in self.results['warnings']:
                    f.write(f"### {warning.get('type', 'Unknown')}\n\n")
                    if 'name' in warning:
                        f.write(f"**Name:** {warning['name']}\n\n")
                    if 'locations' in warning:
                        f.write(f"**Locations:**\n")
                        for loc in warning['locations']:
                            f.write(f"- {loc}\n")
                        f.write("\n")
                    if 'issue' in warning:
                        f.write(f"**Issue:** {warning['issue']}\n\n")
        
        print(f"\nReport saved to: {report_path}")
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("\n" + "="*80)
        print("  KOOPTIMIZER COMPREHENSIVE TESTING")
        print("="*80)
        
        try:
            self.test_duplication_issues()
            self.test_all_roles_pages()
            self.test_database_integrity()
            self.generate_report()
            
            print("\n" + "="*80)
            print("  ALL TESTS COMPLETED")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n[!] ERROR during testing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    tester = ComprehensiveTester()
    tester.run_all_tests()
