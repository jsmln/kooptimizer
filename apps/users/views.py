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
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

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

@login_required_custom
def profile_settings(request):
    user_id = request.session.get('user_id')
    
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
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    context = {'user': user}
    return render(request, 'users/settings.html', context)

@login_required_custom
def update_profile(request):
    if request.method != 'POST':
        return redirect('users:profile_settings')

    user_id = request.session.get('user_id')

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
        user = User.objects.get(user_id=user_id)
        
        # 1. Get Data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        avatar = request.FILES.get('avatar')

        # 2. Update Fields
        if first_name: user.first_name = first_name
        if last_name: user.last_name = last_name
        if email: user.email = email

        # 3. Password Logic
        if new_password:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('users:profile_settings')
            if len(new_password) < 8:
                messages.error(request, "Password must be 8+ chars.")
                return redirect('users:profile_settings')
            user.password_hash = make_password(new_password)

        # 4. Avatar Logic
        if avatar:
            if avatar.size > 2 * 1024 * 1024: # 2MB Limit
                messages.error(request, "Image too large (Max 2MB).")
                return redirect('users:profile_settings')
            user.profile_picture = avatar

        # 5. Save to Database
        user.save()
        
        # 6. Update Session Name (So sidebar updates instantly)
        full_name = f"{user.first_name} {user.last_name}".strip()
        if full_name:
            request.session['username'] = full_name
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
        messages.error(request, "An error occurred while saving changes.")
        return redirect('users:profile_settings')


# ============================================
# PASSWORD RESET VIEWS
# ============================================

def initiate_password_reset(request):
    """Handles the search modal form submission and SENDS REAL OTP"""
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        
        try:
            # 1. Find user by username OR mobile number
            user = User.objects.filter(username=identifier).first()
            if not user:
                user = User.objects.filter(mobile_number=identifier).first()

            if user:
                # 2. Check if user has a mobile number
                if not user.mobile_number:
                    messages.error(request, 'This account does not have a mobile number linked.')
                    return redirect('login')

                # 3. Server-side deduplication: Prevent duplicate OTP requests within 30 seconds
                # Use atomic cache.add() to prevent race conditions - only sets if key doesn't exist
                from django.core.cache import cache
                cache_key = f"otp_reset_{user.user_id}"
                
                # Try to acquire lock atomically - if key exists, another request is already processing
                if not cache.add(cache_key, True, 30):
                    messages.warning(request, 'Please wait before requesting another OTP code. Check your phone for the previous code.')
                    return redirect('login')
                
                # 4. Initialize OTP Service
                otp_service = OTPService(request)
                
                # 5. SEND THE OTP via API (This consumes credits)
                # We use a specific template for password reset to be professional
                msg_template = "KoopTimizer Password Reset: Your verification code is {pin}. Valid for 5 minutes."
                success, error_message = otp_service.send_otp(user.mobile_number, message_template=msg_template)
                
                # If sending failed, remove the cache lock so user can retry
                if not success:
                    cache.delete(cache_key)

                if success:
                    # Store the User ID so we know who we are resetting the password for
                    request.session['reset_user_id'] = user.user_id
                    
                    # Mask Number for display (e.g. *******1234)
                    mobile = user.mobile_number
                    masked = f"*******{mobile[-4:]}" if len(mobile) > 4 else "your number"
                    request.session['reset_masked_mobile'] = masked
                    
                    return redirect('users:perform_password_reset')
                else:
                    # API Failed (No credits, network error, etc)
                    messages.error(request, f'Failed to send SMS: {error_message}')
                    return redirect('login')

            else:
                messages.error(request, 'Account not found.')
                return redirect('login')
                
        except Exception as e:
            print(f"Error in password reset: {e}")
            messages.error(request, 'An error occurred. Please try again.')
            return redirect('login')
    
    return redirect('login')


def perform_password_reset(request):
    """Handles OTP check and Password update"""
    # Security check: ensure we initiated the flow
    if 'reset_user_id' not in request.session:
        return redirect('login')

    step = 'otp' # Default step
    
    if request.method == 'POST':
        current_step = request.POST.get('step')
        
        if current_step == 'verify_otp':
            # Combine the 4 input fields
            input_otp = "".join([
                request.POST.get('otp_1', ''),
                request.POST.get('otp_2', ''),
                request.POST.get('otp_3', ''),
                request.POST.get('otp_4', '')
            ])
            
            # Use the Service to verify (Checks session 'otp_pin' and expiry)
            otp_service = OTPService(request)
            success, message = otp_service.verify_otp(input_otp)
            
            if success:
                step = 'password' # Move to next step
            else:
                messages.error(request, f"Verification failed: {message}")
                step = 'otp'

        elif current_step == 'set_password':
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            
            if new_pass and new_pass == confirm_pass:
                user_id = request.session.get('reset_user_id')
                try:
                    user = User.objects.get(user_id=user_id)
                    
                    # Update password in database
                    user.password_hash = make_password(new_pass) 
                    user.save()
                    
                    # Cleanup Session Data
                    keys_to_delete = ['reset_user_id', 'reset_masked_mobile', 'otp_pin', 'otp_expiry']
                    for key in keys_to_delete:
                        if key in request.session:
                            del request.session[key]
                    
                    messages.success(request, "Password reset successfully! Please login.")
                    return redirect('login')
                except User.DoesNotExist:
                     messages.error(request, "User error.")
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
            # Try multiple query approaches to find events
            # Approach 1: Filter by user_id directly (ForeignKey column)
            events = Event.objects.filter(user_id=user_id)
            event_count = events.count()
            print(f"DEBUG all_events: Approach 1 (user_id={user_id}): Found {event_count} events")
            
            # Approach 2: If no results, try filtering by user's primary key
            if event_count == 0:
                from .models import User
                try:
                    user = User.objects.get(pk=user_id)
                    events = Event.objects.filter(user=user)
                    event_count = events.count()
                    print(f"DEBUG all_events: Approach 2 (user object): Found {event_count} events")
                except User.DoesNotExist:
                    print(f"DEBUG all_events: User with pk={user_id} does not exist")
            
            # Approach 3: If still no results but events exist, show all (for debugging)
            if event_count == 0 and total_events > 0:
                print(f"DEBUG all_events: No events for user_id={user_id}, but {total_events} total events exist. Showing all events for debugging.")
                events = Event.objects.all()
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
            # Always use user_id directly to avoid model mismatch issues with AUTH_USER_MODEL
            # The Event.user ForeignKey points to AUTH_USER_MODEL, which may be different from our custom User model
            try:
                new_event = Event.objects.create(
                    user_id=user_id,  # Use user_id directly - Django will handle the ForeignKey
                    title=data.get("title"),
                    description=data.get("description"),
                    start_date=start_dt,
                    end_date=end_dt
                )
                print(f"✓ Event saved to database: ID={new_event.id}, user_id={user_id}, title={new_event.title}")
            except Exception as db_error:
                print(f"✗ Database save error: {db_error}")
                import traceback
                traceback.print_exc()
                return JsonResponse({"status": "error", "message": f"Failed to save event to database: {str(db_error)}"}, status=500)
            
            # 4. GOOGLE SYNC (Safety Bubble)
            try:
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

                    # Use 'primary' if you shared with the robot email. 
                    # If that fails, replace 'primary' with your actual Gmail address.
                    # Replace 'your.email@gmail.com' with your REAL email address inside the quotes
                    my_calendar_id = 'kooptimizer@gmail.com' 

                    service.events().insert(calendarId=my_calendar_id, body=google_event).execute()
                    print("SUCCESS: Synced to Google Calendar!")
                else:
                    print("WARNING: service_account.json not found.")

            except Exception as google_error:
                print(f"GOOGLE SYNC FAILED (Ignored): {google_error}")

            return JsonResponse({"status": "success"})
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error"}, status=400)
