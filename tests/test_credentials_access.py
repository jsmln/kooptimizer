"""
Comprehensive test suite to verify all API keys and database credentials 
are properly accessible across the application.

Run this test with:
    python test_credentials_access.py
"""

import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.conf import settings
from django.db import connection
from apps.core.services.email_service import EmailService
from apps.core.services.sms_service import SmsService
import requests


class CredentialsTest:
    """Test suite to verify all credentials are accessible"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_header(self, title):
        """Print formatted test section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_result(self, test_name, success, message="", is_warning=False):
        """Print test result with formatting"""
        if is_warning:
            icon = "⚠️ "
            status = "WARNING"
            self.warnings += 1
        elif success:
            icon = "✅"
            status = "PASS"
            self.passed += 1
        else:
            icon = "❌"
            status = "FAIL"
            self.failed += 1
        
        print(f"{icon} {test_name:.<50} {status}")
        if message:
            print(f"   → {message}")
    
    def test_database_credentials(self):
        """Test 1: Verify database connection and credentials"""
        self.print_header("TEST 1: Database Credentials")
        
        try:
            # Test if DATABASE settings are loaded from environment
            db_config = settings.DATABASES['default']
            
            # Check if credentials exist
            has_name = bool(db_config.get('NAME'))
            has_user = bool(db_config.get('USER'))
            has_password = bool(db_config.get('PASSWORD'))
            has_host = bool(db_config.get('HOST'))
            has_port = bool(db_config.get('PORT'))
            
            self.print_result("DB_NAME configured", has_name, 
                            f"Value: {db_config.get('NAME')}")
            self.print_result("DB_USER configured", has_user, 
                            f"Value: {db_config.get('USER')}")
            self.print_result("DB_PASSWORD configured", has_password, 
                            f"Length: {len(db_config.get('PASSWORD', ''))} chars")
            self.print_result("DB_HOST configured", has_host, 
                            f"Value: {db_config.get('HOST')}")
            self.print_result("DB_PORT configured", has_port, 
                            f"Value: {db_config.get('PORT')}")
            
            # Test actual database connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    self.print_result("Database connection successful", True, 
                                    f"PostgreSQL: {version[:50]}...")
            except Exception as e:
                self.print_result("Database connection", False, str(e))
                
        except Exception as e:
            self.print_result("Database configuration", False, str(e))
    
    def test_django_core_settings(self):
        """Test 2: Verify Django core settings"""
        self.print_header("TEST 2: Django Core Settings")
        
        try:
            # SECRET_KEY
            has_secret = bool(settings.SECRET_KEY)
            is_secure = (
                len(settings.SECRET_KEY) >= 50 and 
                not settings.SECRET_KEY.startswith('django-insecure-')
            )
            self.print_result("SECRET_KEY exists", has_secret, 
                            f"Length: {len(settings.SECRET_KEY)} chars")
            if has_secret and not is_secure:
                self.print_result("SECRET_KEY security", False, 
                                "Should be 50+ chars and not prefixed with 'django-insecure-'",
                                is_warning=True)
            
            # DEBUG setting
            debug_value = settings.DEBUG
            self.print_result("DEBUG setting loaded", True, 
                            f"Value: {debug_value}")
            if debug_value:
                self.print_result("DEBUG = True in production?", False,
                                "Set to False for production deployment", 
                                is_warning=True)
            
            # ALLOWED_HOSTS
            has_hosts = bool(settings.ALLOWED_HOSTS)
            self.print_result("ALLOWED_HOSTS configured", has_hosts, 
                            f"Values: {', '.join(settings.ALLOWED_HOSTS[:3])}")
            
            # CSRF_TRUSTED_ORIGINS
            has_csrf = bool(settings.CSRF_TRUSTED_ORIGINS)
            self.print_result("CSRF_TRUSTED_ORIGINS configured", has_csrf, 
                            f"Count: {len(settings.CSRF_TRUSTED_ORIGINS)}")
            
        except Exception as e:
            self.print_result("Django core settings", False, str(e))
    
    def test_recaptcha_credentials(self):
        """Test 3: Verify ReCAPTCHA credentials"""
        self.print_header("TEST 3: ReCAPTCHA Credentials")
        
        try:
            # Check if keys exist
            has_site_key = bool(getattr(settings, 'RECAPTCHA_SITE_KEY', None))
            has_secret_key = bool(getattr(settings, 'RECAPTCHA_SECRET_KEY', None))
            
            self.print_result("RECAPTCHA_SITE_KEY configured", has_site_key, 
                            f"Length: {len(getattr(settings, 'RECAPTCHA_SITE_KEY', ''))} chars")
            self.print_result("RECAPTCHA_SECRET_KEY configured", has_secret_key, 
                            f"Length: {len(getattr(settings, 'RECAPTCHA_SECRET_KEY', ''))} chars")
            
            # Check accessibility in views
            if has_site_key and has_secret_key:
                self.print_result("ReCAPTCHA accessible in settings", True,
                                "Both keys are available")
            
        except Exception as e:
            self.print_result("ReCAPTCHA configuration", False, str(e))
    
    def test_iprog_sms_credentials(self):
        """Test 4: Verify IPROG SMS API credentials"""
        self.print_header("TEST 4: IPROG SMS API Credentials")
        
        try:
            # Check if IPROG_SMS dict exists
            iprog_config = getattr(settings, 'IPROG_SMS', None)
            
            if not iprog_config:
                self.print_result("IPROG_SMS configuration", False, 
                                "IPROG_SMS not found in settings")
                return
            
            # Check each required key
            has_token = bool(iprog_config.get('API_TOKEN'))
            has_url = bool(iprog_config.get('API_URL'))
            has_bulk_url = bool(iprog_config.get('API_URL_BULK'))
            
            self.print_result("IPROG_SMS_API_TOKEN configured", has_token, 
                            f"Length: {len(iprog_config.get('API_TOKEN', ''))} chars")
            self.print_result("IPROG_SMS_API_URL configured", has_url, 
                            f"Value: {iprog_config.get('API_URL')}")
            self.print_result("IPROG_SMS_API_URL_BULK configured", has_bulk_url, 
                            f"Value: {iprog_config.get('API_URL_BULK')}")
            
            # Test SMSService can access credentials
            try:
                sms_service = SmsService()
                self.print_result("SmsService initialization", True,
                                "Service can access IPROG credentials")
            except Exception as e:
                self.print_result("SmsService initialization", False, str(e))
                
        except Exception as e:
            self.print_result("IPROG SMS configuration", False, str(e))
    
    def test_brevo_email_credentials(self):
        """Test 5: Verify Brevo Email API credentials"""
        self.print_header("TEST 5: Brevo Email API Credentials")
        
        try:
            # Check each Brevo setting
            has_api_key = bool(getattr(settings, 'BREVO_API_KEY', None))
            has_api_url = bool(getattr(settings, 'BREVO_API_URL', None))
            has_sender_email = bool(getattr(settings, 'BREVO_SENDER_EMAIL', None))
            has_sender_name = bool(getattr(settings, 'BREVO_SENDER_NAME', None))
            
            self.print_result("BREVO_API_KEY configured", has_api_key, 
                            f"Length: {len(getattr(settings, 'BREVO_API_KEY', ''))} chars")
            self.print_result("BREVO_API_URL configured", has_api_url, 
                            f"Value: {getattr(settings, 'BREVO_API_URL', '')}")
            self.print_result("BREVO_SENDER_EMAIL configured", has_sender_email, 
                            f"Value: {getattr(settings, 'BREVO_SENDER_EMAIL', '')}")
            self.print_result("BREVO_SENDER_NAME configured", has_sender_name, 
                            f"Value: {getattr(settings, 'BREVO_SENDER_NAME', '')}")
            
            # Test EmailService can access credentials
            try:
                email_service = EmailService()
                self.print_result("EmailService initialization", True,
                                "Service can access Brevo credentials")
            except Exception as e:
                self.print_result("EmailService initialization", False, str(e))
                
        except Exception as e:
            self.print_result("Brevo Email configuration", False, str(e))
    
    def test_optional_api_keys(self):
        """Test 6: Verify optional API keys"""
        self.print_header("TEST 6: Optional API Keys")
        
        try:
            # OPTIIC OCR API
            optiic_key = getattr(settings, 'OPTIIC_API_KEY', '')
            has_optiic = bool(optiic_key)
            # OPTIIC is optional, so we pass even if empty
            self.print_result("OPTIIC_API_KEY configured", True, 
                            f"Length: {len(optiic_key)} chars" if has_optiic else "Not set (optional)",
                            is_warning=not has_optiic)
            
            # Ticketmaster API
            ticketmaster_key = getattr(settings, 'TICKETMASTER_API_KEY', '')
            has_ticketmaster = bool(ticketmaster_key)
            self.print_result("TICKETMASTER_API_KEY configured", has_ticketmaster, 
                            f"Length: {len(ticketmaster_key)} chars" if has_ticketmaster else "Not set (optional)")
            
        except Exception as e:
            self.print_result("Optional APIs configuration", False, str(e))
    
    def test_security_settings(self):
        """Test 7: Verify security settings"""
        self.print_header("TEST 7: Security Settings")
        
        try:
            # Session security
            session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
            csrf_secure = getattr(settings, 'CSRF_COOKIE_SECURE', False)
            ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
            hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
            
            self.print_result("SESSION_COOKIE_SECURE setting", True, 
                            f"Value: {session_secure}")
            self.print_result("CSRF_COOKIE_SECURE setting", True, 
                            f"Value: {csrf_secure}")
            self.print_result("SECURE_SSL_REDIRECT setting", True, 
                            f"Value: {ssl_redirect}")
            self.print_result("SECURE_HSTS_SECONDS setting", True, 
                            f"Value: {hsts_seconds}")
            
            # Warnings for production
            if not session_secure or not csrf_secure:
                self.print_result("Production security", False,
                                "Enable SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE for production",
                                is_warning=True)
            
        except Exception as e:
            self.print_result("Security settings", False, str(e))
    
    def test_environment_file(self):
        """Test 8: Verify .env file configuration"""
        self.print_header("TEST 8: Environment File Check")
        
        try:
            env_path = os.path.join(BASE_DIR, '.env')
            env_example_path = os.path.join(BASE_DIR, '.env.example')
            gitignore_path = os.path.join(BASE_DIR, '.gitignore')
            
            # Check if .env exists
            env_exists = os.path.exists(env_path)
            self.print_result(".env file exists", env_exists, 
                            f"Location: {env_path}" if env_exists else "Missing .env file")
            
            # Check if .env.example exists
            example_exists = os.path.exists(env_example_path)
            self.print_result(".env.example exists", example_exists, 
                            "Template file available")
            
            # Check if .env is in .gitignore
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    gitignore_content = f.read()
                    is_ignored = '.env' in gitignore_content or '*.env' in gitignore_content
                    self.print_result(".env in .gitignore", is_ignored, 
                                    "Credentials protected from git" if is_ignored 
                                    else "WARNING: .env should be in .gitignore!")
            
        except Exception as e:
            self.print_result("Environment file check", False, str(e))
    
    def test_credentials_not_hardcoded(self):
        """Test 9: Verify no credentials are hardcoded in settings.py"""
        self.print_header("TEST 9: Hardcoded Credentials Check")
        
        try:
            settings_path = os.path.join(BASE_DIR, 'kooptimizer', 'settings.py')
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patterns that should NOT appear (hardcoded credentials)
            dangerous_patterns = [
                ('xkeysib-', 'Hardcoded Brevo API key'),
                ('a602bb94c96ebbc', 'Hardcoded IPROG token'),
                ('6LeepvEr', 'Hardcoded ReCAPTCHA key'),
                ("'API_TOKEN': '", 'Hardcoded API token'),
                ("PASSWORD': 'postgres'", 'Hardcoded database password'),
            ]
            
            found_issues = []
            for pattern, description in dangerous_patterns:
                if pattern in content:
                    found_issues.append(description)
            
            if found_issues:
                self.print_result("No hardcoded credentials", False, 
                                f"Found: {', '.join(found_issues)}")
            else:
                self.print_result("No hardcoded credentials", True, 
                                "All credentials use environment variables")
            
            # Check if using config() from decouple
            uses_decouple = 'from decouple import config' in content
            self.print_result("Using python-decouple", uses_decouple, 
                            "Proper environment variable management" if uses_decouple 
                            else "Should use python-decouple")
            
        except Exception as e:
            self.print_result("Hardcoded credentials check", False, str(e))
    
    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*70)
        print("  KOOPTIMIZER CREDENTIALS & SECURITY TEST SUITE")
        print("="*70)
        print(f"  Testing environment variable configuration and API accessibility")
        print(f"  Django Settings Module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        print("="*70)
        
        # Run all tests
        self.test_environment_file()
        self.test_django_core_settings()
        self.test_database_credentials()
        self.test_recaptcha_credentials()
        self.test_iprog_sms_credentials()
        self.test_brevo_email_credentials()
        self.test_optional_api_keys()
        self.test_security_settings()
        self.test_credentials_not_hardcoded()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        total_tests = self.passed + self.failed
        pass_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"  ✅ Passed:   {self.passed}")
        print(f"  ❌ Failed:   {self.failed}")
        print(f"  ⚠️  Warnings: {self.warnings}")
        print(f"  📊 Success Rate: {pass_rate:.1f}%")
        print("="*70)
        
        if self.failed == 0:
            print("  🎉 All critical tests passed! Credentials are properly secured.")
        else:
            print("  ⚠️  Some tests failed. Review the issues above.")
        
        print("="*70 + "\n")
        
        return self.failed == 0


if __name__ == '__main__':
    tester = CredentialsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
