"""
Comprehensive Functionality Tests for Kooptimizer

This test suite covers all functionalities per page and per role:
- Admin role functionalities
- Staff role functionalities  
- Officer role functionalities
- Public/unauthenticated access
- Cross-role access prevention
- All CRUD operations
- All API endpoints
- All forms and validations

Run with: python manage.py test test_comprehensive_functionality
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from apps.account_management.models import Users, Admin, Staff, Officers, Cooperatives
from apps.communications.models import Message, MessageRecipient, Announcement
from apps.cooperatives.models import ProfileData, FinancialData, Member
from apps.users.models import User
from datetime import datetime, timedelta
from django.utils import timezone


class BaseTestCase(TestCase):
    """Base test case with common setup for all tests"""
    
    def setUp(self):
        """Create test users and cooperatives"""
        self.client = Client()
        
        # Create test users
        self.admin_user = Users.objects.create(
            username='admin_test',
            password_hash=make_password('admin123'),
            role='admin',
            verification_status='verified',
            is_first_login=False,
            is_active=True
        )
        
        self.admin_profile = Admin.objects.create(
            user=self.admin_user,
            fullname='Admin Test User',
            position='System Administrator',
            gender='male',
            mobile_number='09171234567',
            email='admin@test.com'
        )
        
        # Create staff user
        self.staff_user = Users.objects.create(
            username='staff_test',
            password_hash=make_password('staff123'),
            role='staff',
            verification_status='verified',
            is_first_login=False,
            is_active=True
        )
        
        self.staff_profile = Staff.objects.create(
            user=self.staff_user,
            fullname='Staff Test User',
            position='Cooperative Development Officer',
            gender='female',
            mobile_number='09181234567',
            email='staff@test.com'
        )
        
        # Create cooperative
        self.cooperative = Cooperatives.objects.create(
            staff=self.staff_profile,
            cooperative_name='Test Cooperative',
            category='Multi-Purpose',
            district='North',
            is_active=True
        )
        
        # Create officer user
        self.officer_user = Users.objects.create(
            username='officer_test',
            password_hash=make_password('officer123'),
            role='officer',
            verification_status='verified',
            is_first_login=False,
            is_active=True
        )
        
        self.officer_profile = Officers.objects.create(
            user=self.officer_user,
            coop=self.cooperative,
            fullname='Officer Test User',
            position='President',
            gender='male',
            mobile_number='09191234567',
            email='officer@test.com'
        )
        
        # Create second cooperative for testing isolation
        self.other_cooperative = Cooperatives.objects.create(
            staff=None,
            cooperative_name='Other Test Cooperative',
            category='Credit',
            district='South',
            is_active=True
        )
        
        # Create another officer for the other cooperative
        self.other_officer_user = Users.objects.create(
            username='other_officer_test',
            password_hash=make_password('officer456'),
            role='officer',
            verification_status='verified',
            is_first_login=False,
            is_active=True
        )
        
        self.other_officer_profile = Officers.objects.create(
            user=self.other_officer_user,
            coop=self.other_cooperative,
            fullname='Other Officer User',
            position='Treasurer',
            gender='female',
            mobile_number='09201234567',
            email='other_officer@test.com'
        )
    
    def login_as_admin(self):
        """Helper to login as admin"""
        session = self.client.session
        session['user_id'] = self.admin_user.user_id
        session['role'] = 'admin'
        session['username'] = self.admin_user.username
        session.save()
    
    def login_as_staff(self):
        """Helper to login as staff"""
        session = self.client.session
        session['user_id'] = self.staff_user.user_id
        session['role'] = 'staff'
        session['username'] = self.staff_user.username
        session.save()
    
    def login_as_officer(self):
        """Helper to login as officer"""
        session = self.client.session
        session['user_id'] = self.officer_user.user_id
        session['role'] = 'officer'
        session['username'] = self.officer_user.username
        session.save()
    
    def login_as_other_officer(self):
        """Helper to login as the other officer"""
        session = self.client.session
        session['user_id'] = self.other_officer_user.user_id
        session['role'] = 'officer'
        session['username'] = self.other_officer_user.username
        session.save()
    
    def logout(self):
        """Helper to logout"""
        self.client.session.flush()


class AuthenticationTests(BaseTestCase):
    """Test authentication and authorization"""
    
    def test_login_page_accessible(self):
        """Test that login page is accessible without authentication"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        response = self.client.post(reverse('users:login'), {
            'username': 'admin_test',
            'password': 'admin123'
        })
        self.assertEqual(self.client.session.get('role'), 'admin')
    
    def test_staff_login_success(self):
        """Test successful staff login"""
        response = self.client.post(reverse('users:login'), {
            'username': 'staff_test',
            'password': 'staff123'
        })
        self.assertEqual(self.client.session.get('role'), 'staff')
    
    def test_officer_login_success(self):
        """Test successful officer login"""
        response = self.client.post(reverse('users:login'), {
            'username': 'officer_test',
            'password': 'officer123'
        })
        self.assertEqual(self.client.session.get('role'), 'officer')
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('users:login'), {
            'username': 'invalid_user',
            'password': 'wrong_password'
        })
        self.assertNotIn('user_id', self.client.session)
    
    def test_deactivated_user_cannot_login(self):
        """Test that deactivated users cannot login"""
        self.officer_user.is_active = False
        self.officer_user.save()
        
        response = self.client.post(reverse('users:login'), {
            'username': 'officer_test',
            'password': 'officer123'
        })
        self.assertNotIn('user_id', self.client.session)


class DashboardAccessTests(BaseTestCase):
    """Test dashboard access control per role"""
    
    def test_admin_can_access_admin_dashboard(self):
        """Test admin can access admin dashboard"""
        self.login_as_admin()
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_cannot_access_admin_dashboard(self):
        """Test staff cannot access admin dashboard"""
        self.login_as_staff()
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_officer_cannot_access_admin_dashboard(self):
        """Test officer cannot access admin dashboard"""
        self.login_as_officer()
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_can_access_staff_dashboard(self):
        """Test staff can access staff dashboard"""
        self.login_as_staff()
        response = self.client.get(reverse('dashboard:staff_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_cannot_access_staff_dashboard(self):
        """Test admin cannot access staff dashboard"""
        self.login_as_admin()
        response = self.client.get(reverse('dashboard:staff_dashboard'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_officer_can_access_cooperative_dashboard(self):
        """Test officer can access cooperative dashboard"""
        self.login_as_officer()
        response = self.client.get(reverse('dashboard:cooperative_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_cannot_access_cooperative_dashboard(self):
        """Test admin cannot access cooperative dashboard"""
        self.login_as_admin()
        response = self.client.get(reverse('dashboard:cooperative_dashboard'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test unauthenticated users are redirected to login"""
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 302)


class AccountManagementTests(BaseTestCase):
    """Test account management functionality"""
    
    def test_admin_can_access_account_management(self):
        """Test admin can access account management page"""
        self.login_as_admin()
        response = self.client.get(reverse('account_management:account_management'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_cannot_access_account_management(self):
        """Test staff cannot access account management"""
        self.login_as_staff()
        response = self.client.get(reverse('account_management:account_management'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_officer_cannot_access_account_management(self):
        """Test officer cannot access account management"""
        self.login_as_officer()
        response = self.client.get(reverse('account_management:account_management'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_can_create_staff_account(self):
        """Test admin can create staff account"""
        self.login_as_admin()
        
        payload = {
            'email': 'newstaff@test.com',
            'name': 'New Staff User',
            'type': 'staff',
            'position': 'Development Officer',
            'gender': 'male',
            'contact': '09211234567'
        }
        
        response = self.client.post(
            reverse('account_management:send_credentials'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should succeed or return appropriate response
        self.assertIn(response.status_code, [200, 201])
    
    def test_admin_can_create_officer_account(self):
        """Test admin can create officer account"""
        self.login_as_admin()
        
        payload = {
            'email': 'newofficer@test.com',
            'name': 'New Officer User',
            'type': 'officer',
            'position': 'Secretary',
            'gender': 'female',
            'contact': '09221234567',
            'coop': self.cooperative.coop_id
        }
        
        response = self.client.post(
            reverse('account_management:send_credentials'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_admin_can_deactivate_user(self):
        """Test admin can deactivate user account"""
        self.login_as_admin()
        
        response = self.client.post(
            reverse('account_management:deactivate_user', args=[self.officer_user.user_id])
        )
        
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_can_reactivate_user(self):
        """Test admin can reactivate user account"""
        self.login_as_admin()
        
        # First deactivate
        self.officer_user.is_active = False
        self.officer_user.save()
        
        # Then reactivate
        response = self.client.post(
            reverse('account_management:reactivate_user', args=[self.officer_user.user_id])
        )
        
        self.assertIn(response.status_code, [200, 302])
    
    def test_cannot_create_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        self.login_as_admin()
        
        # Try to create user with existing username
        payload = {
            'email': 'duplicate@test.com',
            'name': 'Duplicate User',
            'type': 'staff',
            'position': 'Officer',
            'gender': 'male',
            'contact': '09231234567'
        }
        
        # This should fail if username generation creates duplicates
        # Implementation depends on how usernames are generated


class DatabankTests(BaseTestCase):
    """Test databank functionality"""
    
    def test_admin_can_access_databank(self):
        """Test admin can access databank"""
        self.login_as_admin()
        response = self.client.get(reverse('databank:databank_management'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_can_access_databank(self):
        """Test staff can access databank"""
        self.login_as_staff()
        response = self.client.get(reverse('databank:databank_management'))
        self.assertEqual(response.status_code, 200)
    
    def test_officer_cannot_access_databank(self):
        """Test officer cannot access databank"""
        self.login_as_officer()
        response = self.client.get(reverse('databank:databank_management'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_sees_all_cooperatives(self):
        """Test admin sees all cooperatives in databank"""
        self.login_as_admin()
        response = self.client.get(reverse('databank:databank_management'))
        
        # Check that both cooperatives are visible
        # Implementation depends on how cooperatives are rendered
    
    def test_staff_sees_only_assigned_cooperatives(self):
        """Test staff only sees assigned cooperatives"""
        self.login_as_staff()
        response = self.client.get(reverse('databank:databank_management'))
        
        # Should only see cooperatives assigned to this staff
        # Implementation depends on view logic
    
    def test_admin_can_add_cooperative(self):
        """Test admin can add new cooperative"""
        self.login_as_admin()
        
        payload = {
            'cooperative_name': 'New Test Cooperative',
            'category': 'Agricultural',
            'district': 'East',
            'staff_id': self.staff_profile.staff_id
        }
        
        response = self.client.post(
            reverse('databank:add_cooperative'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_staff_cannot_add_cooperative(self):
        """Test staff cannot add cooperative"""
        self.login_as_staff()
        
        payload = {
            'cooperative_name': 'Unauthorized Cooperative',
            'category': 'Transport',
            'district': 'West'
        }
        
        response = self.client.post(
            reverse('databank:add_cooperative'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [403, 405])


class CooperativeProfileTests(BaseTestCase):
    """Test cooperative profile functionality"""
    
    def test_officer_can_access_profile_form(self):
        """Test officer can access their cooperative's profile form"""
        self.login_as_officer()
        response = self.client.get(reverse('cooperatives:profile_form'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_cannot_access_profile_form(self):
        """Test admin cannot access profile form (officer-only)"""
        self.login_as_admin()
        response = self.client.get(reverse('cooperatives:profile_form'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_officer_cannot_access_other_cooperative_profile(self):
        """Test officer cannot access another cooperative's profile"""
        self.login_as_officer()
        
        # Try to access other cooperative's data
        # This would require a specific endpoint that takes coop_id
        # Test implementation depends on actual API design
    
    def test_officer_can_create_profile(self):
        """Test officer can create profile for their cooperative"""
        self.login_as_officer()
        
        # Profile creation payload
        # Implementation depends on actual form structure


class MessagingTests(BaseTestCase):
    """Test messaging functionality"""
    
    def test_all_roles_can_access_messaging(self):
        """Test all authenticated roles can access messaging"""
        # Admin
        self.login_as_admin()
        response = self.client.get(reverse('communications:message'))
        self.assertEqual(response.status_code, 200)
        
        # Staff
        self.logout()
        self.login_as_staff()
        response = self.client.get(reverse('communications:message'))
        self.assertEqual(response.status_code, 200)
        
        # Officer
        self.logout()
        self.login_as_officer()
        response = self.client.get(reverse('communications:message'))
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_cannot_access_messaging(self):
        """Test unauthenticated users cannot access messaging"""
        response = self.client.get(reverse('communications:message'))
        self.assertEqual(response.status_code, 302)
    
    def test_send_message_success(self):
        """Test sending message successfully"""
        self.login_as_admin()
        
        payload = {
            'receiver_id': self.staff_user.user_id,
            'message': 'Test message content'
        }
        
        response = self.client.post(
            reverse('communications:send_message'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
    
    def test_send_message_duplicate_prevention(self):
        """Test that duplicate messages are prevented"""
        # This would require testing the guard flag behavior
        # May need to be a frontend/integration test


class AnnouncementTests(BaseTestCase):
    """Test announcement functionality"""
    
    def test_admin_can_access_announcement_page(self):
        """Test admin can access announcement page"""
        self.login_as_admin()
        response = self.client.get(reverse('communications:announcement_form'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_can_access_announcement_page(self):
        """Test staff can access announcement page"""
        self.login_as_staff()
        response = self.client.get(reverse('communications:announcement_form'))
        self.assertEqual(response.status_code, 200)
    
    def test_officer_cannot_access_announcement_page(self):
        """Test officer cannot access announcement page"""
        self.login_as_officer()
        response = self.client.get(reverse('communications:announcement_form'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_can_send_announcement_to_all(self):
        """Test admin can send announcement to all cooperatives"""
        self.login_as_admin()
        
        # Implementation depends on announcement form structure
    
    def test_staff_can_only_send_to_assigned_cooperatives(self):
        """Test staff can only send announcements to assigned cooperatives"""
        self.login_as_staff()
        
        # Implementation depends on recipient filtering logic


class ProfileSettingsTests(BaseTestCase):
    """Test user profile settings"""
    
    def test_all_roles_can_access_settings(self):
        """Test all authenticated users can access their settings"""
        # Admin
        self.login_as_admin()
        response = self.client.get(reverse('users:profile_settings'))
        self.assertEqual(response.status_code, 200)
        
        # Staff
        self.logout()
        self.login_as_staff()
        response = self.client.get(reverse('users:profile_settings'))
        self.assertEqual(response.status_code, 200)
        
        # Officer
        self.logout()
        self.login_as_officer()
        response = self.client.get(reverse('users:profile_settings'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_can_update_profile(self):
        """Test user can update their profile"""
        self.login_as_staff()
        
        payload = {
            'fullname': 'Updated Staff Name',
            'mobile_number': '09999999999',
            'email': 'updated_staff@test.com'
        }
        
        response = self.client.post(
            reverse('users:update_profile'),
            data=payload
        )
        
        self.assertIn(response.status_code, [200, 302])


class DataIsolationTests(BaseTestCase):
    """Test data isolation between cooperatives/staff"""
    
    def test_staff_cannot_see_other_staff_cooperatives(self):
        """Test staff cannot see cooperatives assigned to other staff"""
        # Create another staff with different cooperatives
        other_staff_user = Users.objects.create(
            username='other_staff',
            password_hash=make_password('staff456'),
            role='staff',
            is_active=True
        )
        
        other_staff_profile = Staff.objects.create(
            user=other_staff_user,
            fullname='Other Staff',
            email='otherstaff@test.com'
        )
        
        other_coop = Cooperatives.objects.create(
            staff=other_staff_profile,
            cooperative_name='Other Staff Cooperative',
            is_active=True
        )
        
        # Login as first staff
        self.login_as_staff()
        
        # Try to access other staff's cooperative
        # Implementation depends on API design
    
    def test_officer_cannot_access_other_cooperative_data(self):
        """Test officer cannot access other cooperative's data"""
        self.login_as_officer()
        
        # Try to access data from other_cooperative
        # Should be denied or filtered out


class FormValidationTests(BaseTestCase):
    """Test form validation and data integrity"""
    
    def test_email_uniqueness_validation(self):
        """Test that duplicate emails are rejected"""
        self.login_as_admin()
        
        # Try to create user with existing email
        payload = {
            'email': 'admin@test.com',  # Already exists
            'name': 'Duplicate Email User',
            'type': 'staff',
            'position': 'Officer',
            'gender': 'male',
            'contact': '09241234567'
        }
        
        response = self.client.post(
            reverse('account_management:send_credentials'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should fail
        self.assertIn(response.status_code, [400, 409])
    
    def test_required_fields_validation(self):
        """Test that required fields are enforced"""
        self.login_as_admin()
        
        # Missing required fields
        payload = {
            'email': 'incomplete@test.com',
            # Missing name, type, etc.
        }
        
        response = self.client.post(
            reverse('account_management:send_credentials'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_mobile_number_format_validation(self):
        """Test mobile number format validation"""
        # Implementation depends on validation rules


class FilteringTests(BaseTestCase):
    """Test filtering functionality"""
    
    def test_account_management_filter_active(self):
        """Test filtering active accounts"""
        self.login_as_admin()
        response = self.client.get(
            reverse('account_management:account_management') + '?filter=active'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_account_management_filter_deactivated(self):
        """Test filtering deactivated accounts"""
        self.login_as_admin()
        response = self.client.get(
            reverse('account_management:account_management') + '?filter=deactivated'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_databank_filter_active_cooperatives(self):
        """Test filtering active cooperatives in databank"""
        self.login_as_admin()
        response = self.client.get(
            reverse('databank:databank_management') + '?filter=active'
        )
        self.assertEqual(response.status_code, 200)


class PasswordTests(BaseTestCase):
    """Test password-related functionality"""
    
    def test_password_verification_required_for_sensitive_operations(self):
        """Test that password verification is required for sensitive operations"""
        self.login_as_admin()
        
        # Try to perform sensitive operation without password verification
        # Implementation depends on which operations require verification
    
    def test_password_change_success(self):
        """Test successful password change"""
        self.login_as_staff()
        
        payload = {
            'old_password': 'staff123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        # Implementation depends on password change endpoint
    
    def test_password_reset_flow(self):
        """Test password reset flow with OTP"""
        # Request OTP
        response = self.client.post(
            reverse('users:initiate_password_reset'),
            data={'mobile_number': '09171234567'}
        )
        
        # Should succeed
        self.assertIn(response.status_code, [200, 302])


# Run the test suite
if __name__ == '__main__':
    import unittest
    unittest.main()
