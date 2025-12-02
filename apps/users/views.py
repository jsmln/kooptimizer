from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from psycopg2 import OperationalError, ProgrammingError, InternalError
from django.contrib.auth.hashers import make_password
from .models import User
import requests
from apps.core.services.otp_service import OTPService
import random
import time
import logging
import json
import datetime
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Event

# Google API imports with error handling
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError as e:
    GOOGLE_API_AVAILABLE = False
    print(f"WARNING: Google API client not available: {e}")
    print("Install it with: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib")
    service_account = None
    build = None

import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from .models import User
from apps.account_management.models import Admin, Staff, Officers
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from .models import User
import requests
from apps.core.services.otp_service import OTPService
import random
# Import Custom Token Generator (From the fix we made earlier)
from .tokens import custom_token_generator as default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.urls import reverse

# Import models for getting user email
try:
    from apps.communications.models import Admin, Staff as CommStaff
    from apps.cooperatives.models import Officer
except ImportError:
    # Fallback if models are in different locations
    Admin = None
    CommStaff = None
    Officer = None

# Import models for account management
try:
    from apps.account_management.models import Admin as AccountAdmin, Staff as AccountStaff, Officers as AccountOfficers, Users as AccountUsers
except ImportError:
    AccountAdmin = None
    AccountStaff = None
    AccountOfficers = None
    AccountUsers = None

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_user_email(user_id, role):
    """
    Get the email address for a user based on their role.
    Returns the email from admin, staff, or officers table, or None if not found.
    """
    if not user_id or not role:
        return None
    
    # Check if models are available
    if Admin is None or CommStaff is None or Officer is None:
        print("DEBUG get_user_email: Models not imported. Skipping email lookup.")
        return None
    
    try:
        # Convert user_id to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                return None
        
        if role == 'admin':
            try:
                admin = Admin.objects.get(user_id=user_id)
                email = admin.email if admin and hasattr(admin, 'email') else None
                print(f"DEBUG get_user_email: Admin email for user_id={user_id}: {email}")
                return email
            except (Admin.DoesNotExist, AttributeError) as e:
                print(f"DEBUG get_user_email: Admin not found for user_id={user_id}: {e}")
                return None
        elif role == 'staff':
            try:
                staff = CommStaff.objects.get(user_id=user_id)
                email = staff.email if staff and hasattr(staff, 'email') else None
                print(f"DEBUG get_user_email: Staff email for user_id={user_id}: {email}")
                return email
            except (CommStaff.DoesNotExist, AttributeError) as e:
                print(f"DEBUG get_user_email: Staff not found for user_id={user_id}: {e}")
                return None
        elif role == 'officer':
            try:
                officer = Officer.objects.filter(user_id=user_id).first()
                email = officer.email if officer and hasattr(officer, 'email') else None
                print(f"DEBUG get_user_email: Officer email for user_id={user_id}: {email}")
                return email
            except (AttributeError, Exception) as e:
                print(f"DEBUG get_user_email: Officer lookup error for user_id={user_id}: {e}")
                return None
    except Exception as e:
        print(f"DEBUG get_user_email: Error getting email for user_id={user_id}, role={role}: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return None

# ============================================
# LOGIN & LOGOUT VIEWS
# ============================================

def login_view(request):
    # If user is already logged in, redirect to their dashboard
    if request.session.get('user_id') and request.session.get('is_active', True):
        role = request.session.get('role')
        if role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif role == 'officer':
            return redirect('dashboard:cooperative_dashboard')
        elif role == 'staff':
            return redirect('dashboard:staff_dashboard')
        else:
            return redirect('home')
    
    # Check for lockout on GET as well (for disabling login/home navigation)
    import time
    now = int(time.time())
    lockout_until = request.session.get('login_lockout_until')
    is_locked_out = lockout_until and now < lockout_until

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # --- LOGIN ATTEMPT LIMITING ---
        max_attempts = 5
        lockout_minutes = 1
        failed_attempts = request.session.get('failed_login_attempts', 0)
        lockout_until = request.session.get('login_lockout_until')

        if is_locked_out:
            # Still locked out
            messages.error(request, f'Too many failed login attempts. Please wait {((lockout_until-now)//60)+1} minutes before trying again.')
            return redirect('access_denied')

        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(request, 'Please complete the reCAPTCHA verification.')
            return render(request, 'login.html')
        
        data = {'secret': settings.RECAPTCHA_SECRET_KEY, 'response': recaptcha_response}
        result = None
        
        # Retry logic for reCAPTCHA verification
        max_retries = 3
        timeout = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data=data,
                    timeout=timeout,
                    verify=True,  # Enable SSL verification
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                r.raise_for_status()
                result = r.json()
                break  # Success, exit retry loop
            except requests.exceptions.SSLError as e:
                if attempt < max_retries - 1:
                    # Retry with exponential backoff
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    # Last attempt failed, log and show user-friendly message
                    logger = logging.getLogger(__name__)
                    logger.error(f'reCAPTCHA SSL Error: {e}')
                    messages.error(request, 'Unable to verify reCAPTCHA due to a connection issue. Please check your internet connection and try again.')
                    return render(request, 'login.html')
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    messages.error(request, 'reCAPTCHA verification timed out. Please try again.')
                    return render(request, 'login.html')
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    logger = logging.getLogger(__name__)
                    logger.error(f'reCAPTCHA Request Error: {e}')
                    messages.error(request, 'Unable to verify reCAPTCHA. Please try again later.')
                    return render(request, 'login.html')
        
        if not result:
            messages.error(request, 'Unable to verify reCAPTCHA. Please try again.')
            return render(request, 'login.html')

        if not result.get('success'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'login.html')

        try:
            login_result = User.login_user(username, password)
        except Exception as e:
            messages.error(request, 'Login service unavailable. Please try again later.')
            return render(request, 'login.html')

        if not login_result:
            failed_attempts += 1
            request.session['failed_login_attempts'] = failed_attempts
            if failed_attempts >= max_attempts:
                lockout_until = now + lockout_minutes * 60
                request.session['login_lockout_until'] = lockout_until
                messages.error(request, f'Too many failed login attempts. Please wait {lockout_minutes} minutes before trying again.')
                return redirect('access_denied')
            messages.error(request, f'Invalid login attempt. ({failed_attempts}/{max_attempts})')
            return render(request, 'login.html')

        status_code = login_result['status']
        user_id = login_result['user_id']
        role = login_result['role']
        verification_status = login_result['verification_status']
        is_first_login = login_result['is_first_login']

        if status_code == 'SUCCESS':

            try:
                user_check = User.objects.get(pk=user_id)
                
                if not user_check.is_active:
                    # User is deactivated - Block access immediately
                    messages.error(request, 'Your account has been deactivated. Please contact the administrator.')
                    return redirect('access_denied')
                    
            except User.DoesNotExist:
                messages.error(request, 'Please check your credentials and try again.')
                return render(request, 'login.html')
            

            # Reset failed attempts on successful login
            request.session['failed_login_attempts'] = 0
            request.session['login_lockout_until'] = None
            if is_first_login or verification_status == 'pending':
                request.session['pending_verification_user_id'] = user_id
                request.session['pending_verification_role'] = role
                request.session.pop('user_id', None)
                request.session.pop('role', None)
                try:
                    user = User.objects.get(pk=user_id)
                    full_mobile_number = user.mobile_number
                    masked_number = ""
                    if full_mobile_number and len(full_mobile_number) > 4:
                        masked_number = f"{full_mobile_number[:3]}********{full_mobile_number[-2:]}"
                except User.DoesNotExist:
                    messages.error(request, 'User account not found.')
                    return render(request, 'login.html')
                context = {
                    'show_verification_flow': True,
                    'verification_step': 'start',
                    'masked_mobile_number': masked_number,
                }
                messages.info(request, 'Please complete your account verification to continue.')
                return render(request, 'login.html', context)

            request.session['user_id'] = user_id
            request.session['role'] = role
            request.session['last_activity'] = time.time()
            
            # Set session username to full name from database
            set_session_username(request, user_id, role)
            
            messages.success(request, f'Welcome back, {username}!')
            if role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif role == 'officer':
                return redirect('dashboard:cooperative_dashboard')
            elif role == 'staff':
                return redirect('dashboard:staff_dashboard')
            else:
                messages.error(request, 'Unknown role. Please contact support.')
                return redirect('login')

        elif status_code == 'INVALID_USERNAME_OR_PASSWORD':
            failed_attempts += 1
            request.session['failed_login_attempts'] = failed_attempts
            if failed_attempts >= max_attempts:
                lockout_until = now + lockout_minutes * 60
                request.session['login_lockout_until'] = lockout_until
                messages.error(request, f'Too many failed login attempts. Please wait {lockout_minutes} minutes before trying again.')
                return redirect('access_denied')
            messages.error(request, f'Invalid Username or Password. ({failed_attempts}/{max_attempts})')
        else:
            messages.error(request, 'An internal error occurred. Please contact support.')

    # GET Request
    # Pass lockout info to template for disabling login/home navigation
    context = {'now': now}
    if is_locked_out:
        context['lockout_until'] = lockout_until
        context['lockout_seconds'] = lockout_until - now
    return render(request, 'login.html', context)

def logout_view(request):
    request.session.flush()
    
    # Check if this is a sendBeacon request (from browser close)
    # sendBeacon sends POST but doesn't expect a redirect response
    if request.method == 'POST':
        # Just return success, no redirect needed
        from django.http import JsonResponse
        return JsonResponse({'status': 'success', 'message': 'Logged out'})
    
    # Normal logout (user clicked logout button)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# ============================================
# FIRST LOGIN SETUP (ACTIVATION)
# ============================================

def first_login_setup(request):
    # Check for pending verification session (NOT authenticated session)
    user_id = request.session.get('pending_verification_user_id')
    role = request.session.get('pending_verification_role')
    
    # If no pending verification session, check if already logged in
    if not user_id:
        # If already logged in, redirect to appropriate dashboard
        if request.session.get('user_id'):
            messages.info(request, 'You have already completed setup.')
            user_role = request.session.get('role')
            if user_role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif user_role == 'officer':
                return redirect('dashboard:cooperative_dashboard')
            elif user_role == 'staff':
                return redirect('dashboard:staff_dashboard')
            return redirect('home')
        # Not logged in and no pending verification
        messages.error(request, 'Unauthorized access. Please login first.')
        return redirect('login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user. Please contact support.')
        # Clear invalid pending session
        request.session.pop('pending_verification_user_id', None)
        request.session.pop('pending_verification_role', None)
        return redirect('login')

    full_mobile_number = user.mobile_number
    masked_number = f"{full_mobile_number[:3]}********{full_mobile_number[-2:]}" if full_mobile_number else ""
    
    context = {
        'show_verification_flow': True,
        'verification_step': 'start',
        'masked_mobile_number': masked_number  
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        otp_service = OTPService(request)

        if action == 'send_otp':
            # Server-side deduplication: Prevent duplicate OTP requests within 30 seconds
            # Use atomic cache.add() to prevent race conditions - only sets if key doesn't exist
            from django.core.cache import cache
            cache_key = f"otp_send_{user.user_id}"
            
            # Try to acquire lock atomically - if key exists, another request is already processing
            if not cache.add(cache_key, True, 30):
                messages.warning(request, 'Please wait before requesting another OTP code. Check your phone for the previous code.')
                context['verification_step'] = 'otp' if context.get('verification_step') == 'otp' else 'start'
                return render(request, 'login.html', context)
            
            success, error = otp_service.send_otp(user.mobile_number)
            
            # If sending failed, remove the cache lock so user can retry
            if not success:
                cache.delete(cache_key)
            if success:
                messages.success(request, 'OTP has been sent to your phone.')
                context['verification_step'] = 'otp'
            else:
                messages.error(request, f'Failed to send OTP: {error}')
                context['verification_step'] = 'start'
            
            return render(request, 'login.html', context)
        
        elif action == 'verify_otp':
            otp_1 = request.POST.get('otp_1')
            otp_2 = request.POST.get('otp_2')
            otp_3 = request.POST.get('otp_3')
            otp_4 = request.POST.get('otp_4')

            if not (otp_1 and otp_2 and otp_3 and otp_4):
                messages.error(request, 'Please enter all 4 digits of the OTP.')
                context['verification_step'] = 'otp'
                context['show_otp_form'] = True
                return render(request, 'login.html', context)
            
            otp_code = f"{otp_1}{otp_2}{otp_3}{otp_4}"
            success, error = otp_service.verify_otp(otp_code)
            
            if success:
                messages.success(request, 'Phone number verified successfully.')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context)
            else:
                messages.error(request, f'Invalid OTP code: {error}')
                context['verification_step'] = 'otp'
                return render(request, 'login.html', context)
                
        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            accept_terms = request.POST.get('accept_terms')

            if not accept_terms:
                messages.error(request, 'You must accept the Terms & Conditions and Privacy Policy to continue.')
                context['verification_step'] = 'password'
                context['show_password_form'] = True
                return render(request, 'login.html', context)

            if not new_password or not confirm_password:
                messages.error(request, 'Please enter and confirm your new password.')
                context['verification_step'] = 'password'
                context['show_password_form'] = True
                return render(request, 'login.html', context)
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                context['verification_step'] = 'password'
                context['show_password_form'] = True
                return render(request, 'login.html', context)
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                context['verification_step'] = 'password'
                context['show_password_form'] = True
                return render(request, 'login.html', context)
            # Hash the password
            hashed_password = make_password(new_password)
            
            try:
                User.complete_first_login(
                    user_id=user.user_id,
                    new_password_hash=hashed_password,
                    verification_status='verified'
                )
                # Success! Account is now verified

            except Exception as e:
                messages.error(request, f'An error occurred while updating your profile: {e}')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context)
            
            # Clear pending verification session - user must login with new password
            request.session.pop('pending_verification_user_id', None)
            request.session.pop('pending_verification_role', None)
            
            # Show success page with auto-redirect to login
            context['verification_step'] = 'success'
            return render(request, 'login.html', context)

    return render(request, 'login.html', context)


# ============================================
# PROFILE SETTINGS VIEWS
# ============================================

# Helper decorator
def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_user_profile_data(user_id, role):
    """
    Retrieve user profile data from the appropriate table based on role.
    Returns a dictionary with user data including first_name, last_name, email, etc.
    """
    if not user_id or not role:
        return None
    
    try:
        # Convert user_id to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                return None
        
        # Get base user data
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return None
        
        # Initialize profile data with user data
        profile_data = {
            'user_id': user.user_id,
            'username': user.username,
            'first_name': '',
            'last_name': '',
            'email': '',
            'mobile_number': '',
            'position': '',
            'gender': '',
            'fullname': '',
        }
        
        # Get role-specific data
        if role == 'admin' and AccountAdmin:
            try:
                admin = AccountAdmin.objects.get(user_id=user_id)
                profile_data['fullname'] = admin.fullname or ''
                profile_data['email'] = admin.email or ''
                profile_data['mobile_number'] = admin.mobile_number or ''
                profile_data['position'] = admin.position or ''
                profile_data['gender'] = admin.gender or ''
                
                # Parse fullname into first_name and last_name
                if admin.fullname:
                    name_parts = admin.fullname.strip().split()
                    if len(name_parts) >= 2:
                        profile_data['first_name'] = name_parts[0]
                        profile_data['last_name'] = ' '.join(name_parts[1:])
                    elif len(name_parts) == 1:
                        profile_data['first_name'] = name_parts[0]
            except AccountAdmin.DoesNotExist:
                pass
                
        elif role == 'staff' and AccountStaff:
            try:
                staff = AccountStaff.objects.get(user_id=user_id)
                profile_data['fullname'] = staff.fullname or ''
                profile_data['email'] = staff.email or ''
                profile_data['mobile_number'] = staff.mobile_number or ''
                profile_data['position'] = staff.position or ''
                profile_data['gender'] = staff.gender or ''
                
                # Parse fullname into first_name and last_name
                if staff.fullname:
                    name_parts = staff.fullname.strip().split()
                    if len(name_parts) >= 2:
                        profile_data['first_name'] = name_parts[0]
                        profile_data['last_name'] = ' '.join(name_parts[1:])
                    elif len(name_parts) == 1:
                        profile_data['first_name'] = name_parts[0]
            except AccountStaff.DoesNotExist:
                pass
                
        elif role == 'officer' and AccountOfficers:
            try:
                officer = AccountOfficers.objects.filter(user_id=user_id).first()
                if officer:
                    profile_data['fullname'] = officer.fullname or ''
                    profile_data['email'] = officer.email or ''
                    profile_data['mobile_number'] = officer.mobile_number or ''
                    profile_data['position'] = officer.position or ''
                    profile_data['gender'] = officer.gender or ''
                    
                    # Parse fullname into first_name and last_name
                    if officer.fullname:
                        name_parts = officer.fullname.strip().split()
                        if len(name_parts) >= 2:
                            profile_data['first_name'] = name_parts[0]
                            profile_data['last_name'] = ' '.join(name_parts[1:])
                        elif len(name_parts) == 1:
                            profile_data['first_name'] = name_parts[0]
            except Exception:
                pass
        
        return profile_data
        
    except Exception as e:
        print(f"Error getting user profile data: {e}")
        import traceback
        traceback.print_exc()
        return None

def set_session_username(request, user_id, role):
    """
    Set the session username to the user's full name from the database.
    Falls back to username if no full name is found.
    """
    try:
        profile_data = get_user_profile_data(user_id, role)
        if profile_data:
            fullname = profile_data.get('fullname', '').strip()
            if not fullname and (profile_data.get('first_name') or profile_data.get('last_name')):
                # Fallback to first_name + last_name if fullname is not available
                name_parts = [profile_data.get('first_name', ''), profile_data.get('last_name', '')]
                fullname = ' '.join([p for p in name_parts if p]).strip()
            
            if fullname:
                request.session['username'] = fullname
                request.session.modified = True
                return fullname
    except Exception as e:
        print(f"Error setting session username: {e}")
    
    # If no full name found, keep existing username or use the base username
    if 'username' not in request.session:
        try:
            user = User.objects.get(user_id=user_id)
            request.session['username'] = user.username
            request.session.modified = True
        except User.DoesNotExist:
            pass
    
    return request.session.get('username', '')

@login_required_custom
def profile_settings(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    # Test Account Handling
    if user_id == 9999:
        class DummyUser:
            username = request.session.get('username', 'Test Admin')
            first_name = "Test"
            last_name = "Admin"
            email = "admin@kooptimizer.com"
            profile_picture = None
        context = {'user': DummyUser()}
        return render(request, 'users/settings.html', context)

    try:
        # Get base user data
        user = User.objects.get(user_id=user_id)
        
        # Get role-specific profile data
        profile_data = get_user_profile_data(user_id, role)
        
        if not profile_data:
            messages.error(request, "Profile data not found.")
            return redirect('login')
        
        # Create a combined user object for the template
        class UserProfile:
            def __init__(self, user, profile_data):
                self.user_id = user.user_id
                self.username = user.username
                self.first_name = profile_data.get('first_name', '')
                self.last_name = profile_data.get('last_name', '')
                self.email = profile_data.get('email', '')
                self.mobile_number = profile_data.get('mobile_number', '')
                self.position = profile_data.get('position', '')
                self.gender = profile_data.get('gender', '')
                self.fullname = profile_data.get('fullname', '')
                self.profile_picture = None  # Profile pictures not stored in these tables
        
        user_profile = UserProfile(user, profile_data)
        
        # Update session username with full name for header display
        set_session_username(request, user_id, role)
        
        context = {'user': user_profile}
        return render(request, 'users/settings.html', context)
        
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')
    except Exception as e:
        print(f"Profile settings error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An error occurred while loading profile settings.")
        return redirect('login')

@login_required_custom
def update_profile(request):
    if request.method != 'POST':
        return redirect('users:profile_settings')

    user_id = request.session.get('user_id')
    role = request.session.get('role')

    # Test Account Handling
    if user_id == 9999:
        messages.success(request, "Profile updated! (Simulation)")
        # Simulate name update in session
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        if fname or lname:
             request.session['username'] = f"{fname} {lname}"
        return redirect('users:profile_settings')
    
    try:
        # Convert user_id to int if needed
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                messages.error(request, "Invalid user ID.")
                return redirect('users:profile_settings')
        
        # Get base user data
        user = User.objects.get(user_id=user_id)
        
        # 1. Get Form Data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        avatar = request.FILES.get('avatar')

        # 2. Update Password in User table if provided (blank passwords are allowed - no update)
        if new_password and new_password.strip():
            # Only validate and update if password is provided
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('users:profile_settings')
            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
                return redirect('users:profile_settings')
            user.password_hash = make_password(new_password)
            user.save()

        # 3. Update role-specific profile data
        fullname = f"{first_name} {last_name}".strip() if first_name or last_name else ''
        profile_updated = False
        
        if role == 'admin' and AccountAdmin and AccountUsers:
            try:
                admin = AccountAdmin.objects.get(user_id=user_id)
                # Always update fields (even if empty, to allow clearing)
                admin.fullname = fullname
                admin.email = email
                admin.save()
                profile_updated = True
            except AccountAdmin.DoesNotExist:
                # Create admin profile if it doesn't exist
                try:
                    account_user = AccountUsers.objects.get(user_id=user_id)
                    AccountAdmin.objects.create(
                        user=account_user,
                        fullname=fullname,
                        email=email
                    )
                    profile_updated = True
                except AccountUsers.DoesNotExist:
                    print(f"Error: AccountUsers not found for user_id={user_id}")
                except Exception as e:
                    print(f"Error creating admin profile: {e}")
                    import traceback
                    traceback.print_exc()
                    
        elif role == 'staff' and AccountStaff and AccountUsers:
            try:
                staff = AccountStaff.objects.get(user_id=user_id)
                # Always update fields (even if empty, to allow clearing)
                staff.fullname = fullname
                staff.email = email
                staff.save()
                profile_updated = True
            except AccountStaff.DoesNotExist:
                # Create staff profile if it doesn't exist
                try:
                    account_user = AccountUsers.objects.get(user_id=user_id)
                    AccountStaff.objects.create(
                        user=account_user,
                        fullname=fullname,
                        email=email
                    )
                    profile_updated = True
                except AccountUsers.DoesNotExist:
                    print(f"Error: AccountUsers not found for user_id={user_id}")
                except Exception as e:
                    print(f"Error creating staff profile: {e}")
                    import traceback
                    traceback.print_exc()
                    
        elif role == 'officer' and AccountOfficers:
            try:
                officer = AccountOfficers.objects.filter(user_id=user_id).first()
                if officer:
                    # Always update fields (even if empty, to allow clearing)
                    officer.fullname = fullname
                    officer.email = email
                    officer.save()
                    profile_updated = True
                else:
                    # Note: Officers need a coop_id, so we can't create without it
                    print(f"Warning: Officer profile not found for user_id={user_id}")
            except Exception as e:
                print(f"Error updating officer profile: {e}")
                import traceback
                traceback.print_exc()
        
        # Log if profile wasn't updated (for debugging)
        if not profile_updated and role in ['admin', 'staff', 'officer']:
            print(f"Warning: Profile not updated for user_id={user_id}, role={role}")
            print(f"AccountAdmin available: {AccountAdmin is not None}")
            print(f"AccountStaff available: {AccountStaff is not None}")
            print(f"AccountOfficers available: {AccountOfficers is not None}")
        
        # 4. Avatar Logic (if profile pictures are stored elsewhere)
        # Note: Profile pictures are not in the admin/staff/officers tables
        # This would need to be handled separately if you have a profile_picture field
        
        # 5. Update Session Name (So sidebar updates instantly)
        if fullname:
            request.session['username'] = fullname
        else:
            request.session['username'] = user.username
            
        request.session.modified = True

        messages.success(request, "Profile updated successfully!")
        return redirect('users:profile_settings')

    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')
    except Exception as e:
        print(f"Update Error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An error occurred while saving changes.")
        return redirect('users:profile_settings')


# ============================================
# PASSWORD RESET VIEWS
# ============================================

def initiate_password_reset(request):
    """Handles the search modal form submission"""
    if request.method == 'POST':
        reset_method = request.POST.get('reset_method')
        identifier = request.POST.get('identifier', '').strip()
        
        try:
            user = None
            
            # --- OPTION A: EMAIL ---
            if reset_method == 'email':
                # Search in profile tables first since User table doesn't have email
                admin = Admin.objects.filter(email__iexact=identifier).first()
                if admin: user = admin.user
                
                if not user:
                    staff = Staff.objects.filter(email__iexact=identifier).first()
                    if staff: user = staff.user

                if not user:
                    officer = Officers.objects.filter(email__iexact=identifier).first()
                    if officer: user = officer.user

                if not user:
                    messages.error(request, 'No account found with this email address.')
                    return redirect('login')

                # Generate Link
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                reset_link = request.build_absolute_uri(
                    reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                subject = "Reset Your KoopTimizer Password"
                message = f"Click the link to reset your password: {reset_link}"
                
                send_mail(subject, message, settings.EMAIL_HOST_USER, [identifier], fail_silently=False)
                
                messages.success(request, f"We've sent a password reset link to {identifier}")
                return redirect('login')

            # --- OPTION B: SMS (OTP) ---
            elif reset_method == 'sms':
                # Find User by Username or Mobile
                user = User.objects.filter(username=identifier).first()
                if not user:
                    user = User.objects.filter(mobile_number=identifier).first()

                if user and user.mobile_number:
                    # --- CREDIT SAVER LOGIC ---
                    # If testing, skip API to save credits
                    otp_service = OTPService(request)
                    msg_template = "KoopTimizer Reset Code: {pin}"
                    
                    if identifier.lower() in ['test', 'admin', 'sample']: 
                        # Fake send for testing
                        print(f"\n[CREDIT SAVER] OTP for {user.username}: {otp_service._generate_pin()} (Not sent via SMS)\n")
                        # We still need to generate a real session OTP, so we call internal method manually
                        # But to keep it simple, let's just call send_otp and rely on console logs if API fails
                        success, error_msg = otp_service.send_otp(user.mobile_number, message_template=msg_template)
                    else:
                        # Real Send
                        success, error_msg = otp_service.send_otp(user.mobile_number, message_template=msg_template)

                    if success:
                        request.session['reset_user_id'] = user.user_id
                        masked = f"*******{user.mobile_number[-4:]}" if len(user.mobile_number) > 4 else "your number"
                        request.session['reset_masked_mobile'] = masked
                        return redirect('users:perform_password_reset')
                    else:
                        messages.error(request, f'Failed to send SMS: {error_msg}')
                        return redirect('login')
                else:
                    messages.error(request, 'Account not found or no mobile number linked.')
                    return redirect('login')
            
        except Exception as e:
            print(f"Reset Error: {e}")
            messages.error(request, 'An error occurred. Please try again.')
            return redirect('login')
    
    return redirect('login')


def password_reset_confirm(request, uidb64, token):
    """Handles link clicked from Email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['reset_user_id'] = user.user_id
        request.session['reset_via_email'] = True
        return redirect('users:perform_password_reset')
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('login')


def perform_password_reset(request):
    """Handles OTP verify and Password Change"""
    if 'reset_user_id' not in request.session:
        return redirect('login')

    step = 'password' if request.session.get('reset_via_email') else 'otp'
    
    if request.method == 'POST':
        current_step = request.POST.get('step')
        
        if current_step == 'verify_otp':
            input_otp = "".join([
                request.POST.get('otp_1', ''),
                request.POST.get('otp_2', ''),
                request.POST.get('otp_3', ''),
                request.POST.get('otp_4', '')
            ])
            
            otp_service = OTPService(request)
            success, message = otp_service.verify_otp(input_otp)
            
            if success:
                step = 'password'
            else:
                messages.error(request, f"Verification failed: {message}")
                step = 'otp'

        elif current_step == 'set_password':
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if new_pass and new_pass == confirm_pass:
                if len(new_pass) < 8:
                     messages.error(request, "Password must be at least 8 characters.")
                else:
                    user_id = request.session.get('reset_user_id')
                    try:
                        # 1. Hash the password
                        hashed_password = make_password(new_pass)
                        
                        # 2. DIRECT SQL UPDATE
                        # This forces the database to update, ignoring any Model issues
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                                [hashed_password, user_id]
                            )
                        
                        # 3. Cleanup
                        keys = ['reset_user_id', 'reset_masked_mobile', 'otp_pin', 'otp_expiry', 'reset_via_email']
                        for k in keys:
                            if k in request.session: del request.session[k]
                        
                        messages.success(request, "Password reset successfully! Please login.")
                        return redirect('login')

                    except Exception as e:
                         print(f"Save Error: {e}")
                         messages.error(request, "Database error while saving password.")
                         return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
                step = 'password'

    context = {
        'step': step,
        'masked_mobile': request.session.get('reset_masked_mobile')
    }
    return render(request, 'users/password_reset.html', context)

def all_events(request):
    # Get user_id from session
    user_id = request.session.get('user_id')
    
    print(f"DEBUG all_events: user_id from session = {user_id}")
    
    # If we have a valid user_id, filter by user_id
    try:
        # First, check total events in database for debugging
        total_events = Event.objects.count()
        print(f"DEBUG all_events: Total events in database: {total_events}")
        
        if user_id:
            # Filter by user_id - check both the FK column and description field (workaround)
            # Since FK points to auth_user but our users are in custom users table,
            # we need to check both user_id and description for USER_ID:xxx pattern
            events_by_fk = Event.objects.filter(user_id=user_id)
            # Also check description for USER_ID:xxx pattern as fallback
            all_events_list = list(Event.objects.all())
            events_by_desc = [e for e in all_events_list if e.description and f"USER_ID:{user_id}" in e.description]
            
            # Combine both, removing duplicates
            event_ids = set(events_by_fk.values_list('id', flat=True))
            event_ids.update([e.id for e in events_by_desc])
            events = Event.objects.filter(id__in=event_ids) if event_ids else Event.objects.none()
            
            event_count = events.count()
            print(f"DEBUG all_events: Filtering by user_id={user_id}: Found {event_count} events")
        else:
            # If not logged in, show all events
            events = Event.objects.all()
            print(f"DEBUG all_events: No user_id, showing all {events.count()} events")
    except Exception as e:
        print(f"ERROR all_events: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

    out = []
    for event in events:
        # Format dates for FullCalendar (ISO 8601 format)
        # FullCalendar can handle both date-only and datetime formats
        if event.start_date:
            # Convert to timezone-aware if needed, then format as ISO
            if timezone.is_naive(event.start_date):
                start_dt = timezone.make_aware(event.start_date, timezone.get_current_timezone())
            else:
                start_dt = event.start_date
            start_str = start_dt.isoformat()
        else:
            start_str = None
            
        if event.end_date:
            # Convert to timezone-aware if needed, then format as ISO
            if timezone.is_naive(event.end_date):
                end_dt = timezone.make_aware(event.end_date, timezone.get_current_timezone())
            else:
                end_dt = event.end_date
            end_str = end_dt.isoformat()
        else:
            end_str = None
        
        event_data = {
            'title': event.title,
            'id': event.id,
            'start': start_str,
            'end': end_str,
        }
        
        if event.description:
            event_data['description'] = event.description
        
        out.append(event_data)
    
    print(f"DEBUG all_events: Returning {len(out)} events for user_id={user_id}")
    if len(out) > 0:
        print(f"DEBUG all_events: First event: {out[0]}")
    
    return JsonResponse(out, safe=False)

@csrf_exempt
def add_event(request):
    if request.method == "POST":
        try:
            # 1. SETUP USER_ID - Get user_id from session
            # We'll use user_id directly to avoid model mismatch issues with AUTH_USER_MODEL
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)
            print(f"DEBUG add_event: user_id from session = {user_id}")

            # 2. PREPARE DATA
            data = json.loads(request.body)
            raw_start = data.get("start")
            raw_end = data.get("end")

            # --- FIX: SMART DATE FORMATTER ---
            # If date is just "2025-11-30", turn it into "2025-11-30T00:00:00"
            if 'T' not in raw_start:
                final_start = f"{raw_start}T08:00:00" # Default to 8 AM
            else:
                final_start = raw_start if len(raw_start) > 16 else f"{raw_start}:00"

            if 'T' not in raw_end:
                final_end = f"{raw_end}T09:00:00" # Default to 1 hour later
            else:
                final_end = raw_end if len(raw_end) > 16 else f"{raw_end}:00"
            # --------------------------------

            # Parse datetime strings and make them timezone-aware
            # Parse the datetime strings
            try:
                # Try ISO format parsing
                start_dt = datetime.datetime.fromisoformat(final_start.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(final_end.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # Fallback: parse manually
                try:
                    # Format: "2025-11-29T10:27:00" or "2025-11-29T10:27:00+08:00"
                    if '+' in final_start or final_start.endswith('Z'):
                        start_dt = datetime.datetime.fromisoformat(final_start.replace('Z', '+00:00'))
                    else:
                        start_dt = datetime.datetime.strptime(final_start, "%Y-%m-%dT%H:%M:%S")
                    
                    if '+' in final_end or final_end.endswith('Z'):
                        end_dt = datetime.datetime.fromisoformat(final_end.replace('Z', '+00:00'))
                    else:
                        end_dt = datetime.datetime.strptime(final_end, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    # Last resort: use current time
                    start_dt = timezone.now()
                    end_dt = timezone.now()
            
            # Make timezone-aware if naive
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())

            # 3. SAVE TO DB
            # The Event.user ForeignKey points to AUTH_USER_MODEL (Django's default User in auth_user table),
            # but our users are in the custom users table. We'll use raw SQL to insert with user_id=NULL
            # and then update it, or use a workaround to store the custom user_id.
            try:
                # Use raw SQL to insert event, setting user_id to NULL to avoid FK constraint violation
                # We'll store the custom user_id in the description or use a workaround
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO app_events (user_id, title, description, start_date, end_date)
                        VALUES (NULL, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        data.get("title"),
                        data.get("description", ""),
                        start_dt,
                        end_dt
                    ])
                    event_id = cursor.fetchone()[0]
                    
                    # Try to update user_id - this will fail if FK constraint is enforced at DB level
                    # If it fails, we'll store user_id in description as a workaround
                    try:
                        cursor.execute(
                            "UPDATE app_events SET user_id = %s WHERE id = %s",
                            [user_id, event_id]
                        )
                        print(f"✓ Event saved to database: ID={event_id}, user_id={user_id}, title={data.get('title')}")
                    except Exception as fk_error:
                        # FK constraint violation - store user_id in description as metadata
                        # Format: "USER_ID:47|original description"
                        original_desc = data.get("description", "")
                        desc_with_user = f"USER_ID:{user_id}|{original_desc}" if original_desc else f"USER_ID:{user_id}"
                        cursor.execute(
                            "UPDATE app_events SET description = %s WHERE id = %s",
                            [desc_with_user, event_id]
                        )
                        print(f"✓ Event saved (user_id in description): ID={event_id}, user_id={user_id}, title={data.get('title')}")
                
                new_event = Event.objects.get(id=event_id)
                
            except Exception as db_error:
                print(f"✗ Database save error: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({"status": "error", "message": f"Failed to save event to database: {str(db_error)}"}, status=500)
            
            # 4. GOOGLE SYNC (Safety Bubble)
            try:
                # Get user's email based on their role
                user_role = request.session.get('role')
                user_email = get_user_email(user_id, user_role)
                
                if not user_email:
                    print(f"DEBUG add_event: No email found for user_id={user_id}, role={user_role}. Skipping Google Calendar sync.")
                elif not GOOGLE_API_AVAILABLE:
                    print("WARNING: Google API client not available. Skipping Google Calendar sync.")
                    print("Install it with: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib")
                else:
                    SCOPES = ['https://www.googleapis.com/auth/calendar']
                    SERVICE_ACCOUNT_FILE = 'service_account.json' 
                    
                    if os.path.exists(SERVICE_ACCOUNT_FILE):
                        creds = service_account.Credentials.from_service_account_file(
                            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                        service = build('calendar', 'v3', credentials=creds)

                        google_event = {
                            'summary': data.get("title"),
                            'description': data.get("description"),
                            'start': {
                                'dateTime': final_start, # Uses the fixed format
                                'timeZone': 'Asia/Manila',
                            },
                            'end': {
                                'dateTime': final_end,   # Uses the fixed format
                                'timeZone': 'Asia/Manila',
                            },
                        }

                        # Use the user's email as the calendar ID
                        # For domain-wide delegation, the service account can impersonate the user
                        # If using a regular service account, you may need to share the calendar with the service account email
                        calendar_id = user_email
                        print(f"DEBUG add_event: Syncing to Google Calendar for user: {calendar_id}")

                        try:
                            service.events().insert(calendarId=calendar_id, body=google_event).execute()
                            print(f"SUCCESS: Synced to Google Calendar for {calendar_id}!")
                        except Exception as calendar_error:
                            # If direct access fails, try using 'primary' as fallback
                            print(f"WARNING: Failed to sync to {calendar_id}, trying 'primary': {calendar_error}")
                            try:
                                service.events().insert(calendarId='primary', body=google_event).execute()
                                print("SUCCESS: Synced to Google Calendar (primary)!")
                            except Exception as fallback_error:
                                print(f"GOOGLE SYNC FAILED: {fallback_error}")
                    else:
                        print("WARNING: service_account.json not found.")

            except Exception as google_error:
                print(f"GOOGLE SYNC FAILED (Ignored): {google_error}")

            return JsonResponse({"status": "success"})
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def update_event(request, event_id):
    if request.method == "PUT" or request.method == "POST":
        try:
            # 1. SETUP USER_ID - Get user_id from session
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)
            print(f"DEBUG update_event: user_id from session = {user_id}, event_id = {event_id}")

            # 2. VERIFY EVENT EXISTS AND BELONGS TO USER
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Event not found"}, status=404)
            
            # Check if event belongs to user (check both FK and description workaround)
            event_belongs_to_user = False
            if event.user_id == user_id:
                event_belongs_to_user = True
            elif event.description and f"USER_ID:{user_id}" in event.description:
                event_belongs_to_user = True
            
            if not event_belongs_to_user:
                print(f"DEBUG update_event: Event {event_id} does not belong to user_id {user_id}")
                return JsonResponse({"status": "error", "message": "You don't have permission to edit this event"}, status=403)

            # 3. PREPARE DATA
            data = json.loads(request.body)
            raw_start = data.get("start")
            raw_end = data.get("end")

            # --- SMART DATE FORMATTER ---
            # Handle None or empty strings
            if not raw_start:
                # If no start date provided, keep existing start_date
                final_start = event.start_date.isoformat() if event.start_date else None
            elif 'T' not in str(raw_start):
                final_start = f"{raw_start}T08:00:00"
            else:
                final_start = raw_start if len(raw_start) > 16 else f"{raw_start}:00"

            if not raw_end:
                # If no end date provided, keep existing end_date
                final_end = event.end_date.isoformat() if event.end_date else None
            elif 'T' not in str(raw_end):
                final_end = f"{raw_end}T09:00:00"
            else:
                final_end = raw_end if len(raw_end) > 16 else f"{raw_end}:00"

            # Parse datetime strings and make them timezone-aware
            if final_start:
                try:
                    start_dt = datetime.datetime.fromisoformat(final_start.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        if '+' in final_start or final_start.endswith('Z'):
                            start_dt = datetime.datetime.fromisoformat(final_start.replace('Z', '+00:00'))
                        else:
                            start_dt = datetime.datetime.strptime(final_start, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        start_dt = event.start_date or timezone.now()
                
                # Make timezone-aware if naive (regardless of which parsing method succeeded)
                if start_dt and timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            else:
                start_dt = event.start_date  # Keep existing if not provided

            if final_end:
                try:
                    end_dt = datetime.datetime.fromisoformat(final_end.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        if '+' in final_end or final_end.endswith('Z'):
                            end_dt = datetime.datetime.fromisoformat(final_end.replace('Z', '+00:00'))
                        else:
                            end_dt = datetime.datetime.strptime(final_end, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        end_dt = event.end_date or timezone.now()
                
                # Make timezone-aware if naive (regardless of which parsing method succeeded)
                if end_dt and timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
            else:
                end_dt = event.end_date  # Keep existing if not provided

            # 4. UPDATE EVENT
            event.title = data.get("title", event.title)
            event.description = data.get("description", event.description)
            if start_dt:
                event.start_date = start_dt
            if end_dt:
                event.end_date = end_dt
            event.save()
            
            print(f"✓ Event updated: ID={event.id}, title={event.title}")

            # 5. GOOGLE SYNC (if applicable)
            try:
                # Get user's email based on their role
                user_role = request.session.get('role')
                user_email = get_user_email(user_id, user_role)
                
                if not user_email:
                    print(f"DEBUG update_event: No email found for user_id={user_id}, role={user_role}. Skipping Google Calendar sync.")
                elif not GOOGLE_API_AVAILABLE:
                    print("WARNING: Google API client not available. Skipping Google Calendar sync.")
                    print("Install it with: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib")
                else:
                    SCOPES = ['https://www.googleapis.com/auth/calendar']
                    SERVICE_ACCOUNT_FILE = 'service_account.json' 
                    
                    if os.path.exists(SERVICE_ACCOUNT_FILE):
                        creds = service_account.Credentials.from_service_account_file(
                            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                        service = build('calendar', 'v3', credentials=creds)

                        google_event = {
                            'summary': data.get("title"),
                            'description': data.get("description"),
                            'start': {
                                'dateTime': final_start,
                                'timeZone': 'Asia/Manila',
                            },
                            'end': {
                                'dateTime': final_end,
                                'timeZone': 'Asia/Manila',
                            },
                        }

                        # Use the user's email as the calendar ID
                        calendar_id = user_email
                        print(f"DEBUG update_event: Syncing to Google Calendar for user: {calendar_id}")

                        try:
                            # Note: For updates, you'd need to track google_event_id to update existing events
                            # For now, we'll create a new event (which may create duplicates)
                            # TODO: Store google_event_id in Event model to enable proper updates
                            service.events().insert(calendarId=calendar_id, body=google_event).execute()
                            print(f"SUCCESS: Synced updated event to Google Calendar for {calendar_id}!")
                        except Exception as calendar_error:
                            # If direct access fails, try using 'primary' as fallback
                            print(f"WARNING: Failed to sync to {calendar_id}, trying 'primary': {calendar_error}")
                            try:
                                service.events().insert(calendarId='primary', body=google_event).execute()
                                print("SUCCESS: Synced to Google Calendar (primary)!")
                            except Exception as fallback_error:
                                print(f"GOOGLE SYNC FAILED: {fallback_error}")
                    else:
                        print("WARNING: service_account.json not found.")
            except Exception as google_error:
                print(f"GOOGLE SYNC FAILED (Ignored): {google_error}")

            return JsonResponse({"status": "success"})
            
        except Exception as e:
            print(f"ERROR update_event: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error"}, status=400)
def contact_view(request):
    if request.method == 'POST':
        # 1. Get Data from Form
        name = request.POST.get('name')
        user_email = request.POST.get('email') # The user's email
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message_body = request.POST.get('message')

        # 2. Prepare Email Content
        email_subject = f"New Inquiry: {subject}"
        
        # We put the user's details inside the message body so you know who sent it
        full_message = f"""
        You have received a new message via the KoopTimizer Contact Form.

        --------------------------------------------------
        Sender Name:  {name}
        Sender Email: {user_email}
        Phone Number: {phone}
        --------------------------------------------------

        Message:
        {message_body}
        """

        try:
            # 3. Construct the Email Object
            email = EmailMessage(
                subject=email_subject,
                body=full_message,
                from_email=settings.EMAIL_HOST_USER, # MUST be your verified Gmail
                to=['kooptimizer@gmail.com'],        # Sending to yourself
                reply_to=[user_email]                # <--- THE FIX: Replies go to the user
            )
            
            # 4. Send
            email.send(fail_silently=False)
            
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
            
        except Exception as e:
            # Print error to console for debugging
            print(f"Email Error: {e}")
            messages.error(request, "Failed to send message. Please try again later.")
            return redirect('contact')

    return render(request, 'contact.html')
