# Make sure to import these at the top of your views.py
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from psycopg2 import OperationalError, ProgrammingError, InternalError
from django.contrib.auth.hashers import make_password
from .models import User
import requests
from apps.core.services.otp_service import OTPService

# This is the user login view
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
        data = {'secret': settings.RECAPTCHA_SECRET_KEY, 'response': recaptcha_response}
        try:
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            r.raise_for_status()
            result = r.json()
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Server error during verification: {e}')
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
    # Clear all session data
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
    masked_number = ""

    if full_mobile_number and len(full_mobile_number) > 4:
        masked_number = f"{full_mobile_number[:3]}********{full_mobile_number[-2:]}"
    
    context = {
        'show_verification_flow': True,
        'verification_step': 'start',
        'masked_mobile_number': masked_number  
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        
        otp_service = OTPService(request)

        if action == 'send_otp':
            success, error = otp_service.send_otp(user.mobile_number)
            
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

            # Check if all fields were filled
            if not (otp_1 and otp_2 and otp_3 and otp_4):
                messages.error(request, 'Please enter all 4 digits of the OTP.')
                context['verification_step'] = 'otp'
                context['show_otp_form'] = True
                return render(request, 'login.html', context)
            
            # Combine them into the single string your service expects
            otp_code = f"{otp_1}{otp_2}{otp_3}{otp_4}"

            otp_service = OTPService(request)
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

# Helper decorator to check if logged in
def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required_custom
def profile_settings(request):
    user_id = request.session.get('user_id')
    
    # --- HANDLER FOR TEST ACCOUNT ---
    if user_id == 9999:
        # Create a fake user object just for the template
        class DummyUser:
            username = request.session.get('username', 'Test Admin')
            first_name = "Test"
            last_name = "Admin"
            email = "admin@kooptimizer.com"
            profile_picture = None
        
        context = {'user': DummyUser()}
        return render(request, 'users/settings.html', context)
    # --------------------------------

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    context = {
        'user': user,
    }
    return render(request, 'users/settings.html', context)

@login_required_custom
def update_profile(request):
    if request.method != 'POST':
        return redirect('users:profile_settings')

    user_id = request.session.get('user_id')

    # --- HANDLER FOR TEST ACCOUNT ---
    if user_id == 9999:
        messages.success(request, "Profile updated! (This is a simulation for the Test Account)")
        # Simulate name change in session
        if request.POST.get('first_name'):
             request.session['username'] = request.POST.get('first_name')
        return redirect('users:profile_settings')
    # --------------------------------
    
    try:
        user = User.objects.get(user_id=user_id)
        
        # 1. Get Form Data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        avatar = request.FILES.get('avatar')

        # 2. Update Basic Info
        if first_name: user.first_name = first_name
        if last_name: user.last_name = last_name
        if email: user.email = email

        # 3. Handle Password Change
        if new_password:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('users:profile_settings')
            
            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
                return redirect('users:profile_settings')
                
            user.password_hash = make_password(new_password) # Note: Your model might use 'password' or 'password_hash'

        # 4. Handle Avatar Upload
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                messages.error(request, "Profile picture too large (Max 2MB).")
                return redirect('users:profile_settings')
            
            user.profile_picture = avatar

        user.save()
        
        # Update Session Name
        request.session['username'] = f"{user.first_name} {user.last_name}" 
        request.session.modified = True

        messages.success(request, "Profile updated successfully!")
        return redirect('users:profile_settings')

    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')
    except Exception as e:
        print(f"Error updating profile: {e}")
        messages.error(request, "An error occurred while saving changes.")
        return redirect('users:profile_settings')