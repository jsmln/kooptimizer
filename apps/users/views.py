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

# ============================================
# LOGIN & LOGOUT VIEWS
# ============================================

def login_view(request):
    # If user is already logged in, redirect to their dashboard
    if request.session.get('user_id'):
        role = request.session.get('role')
        if role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif role == 'officer':
            return redirect('dashboard:cooperative_dashboard')
        elif role == 'staff':
            return redirect('dashboard:staff_dashboard')
        else:
            return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # ============================================================
        # 🛠️ HARDCODED TEST ACCOUNT (Remove in Production)
        # ============================================================
        if username == 'testadmin' and password == '12345':
            # Set dummy session data required by your Dashboard
            request.session['user_id'] = 9999 
            request.session['username'] = 'Administrator' 
            request.session['role'] = 'admin'
            
            messages.success(request, 'Welcome back, Administrator! (Bypassed)')
            return redirect('dashboard:admin_dashboard')
        # ============================================================

        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
        data = {'secret': settings.RECAPTCHA_SECRET_KEY, 'response': recaptcha_response}
        try:
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            r.raise_for_status()
            result = r.json()
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Server error during verification: {e}')
            return render(request, 'login.html') # Fixed Path

        if not result.get('success'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'login.html') # Fixed Path

        # Call the stored procedure via User model helper
        try:
            login_result = User.login_user(username, password)
        except Exception as e:
            messages.error(request, 'Login service unavailable. Please try again later.')
            return render(request, 'login.html') # Fixed Path

        if not login_result:
            messages.error(request, 'Invalid login attempt.')
            return render(request, 'login.html') # Fixed Path

        status_code = login_result['status']
        user_id = login_result['user_id']
        role = login_result['role']
        verification_status = login_result['verification_status']
        is_first_login = login_result['is_first_login']

        if status_code == 'SUCCESS':
            # Handle first login or pending verification - DO NOT log them in yet
            if is_first_login or verification_status == 'pending':
                request.session['pending_verification_user_id'] = user_id
                request.session['pending_verification_role'] = role
                # Clear any accidental auth session
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
                    return render(request, 'login.html') # Fixed Path
                
                context = {
                    'show_verification_flow': True,
                    'verification_step': 'start',
                    'masked_mobile_number': masked_number,
                }
                messages.info(request, 'Please complete your account verification to continue.')
                return render(request, 'login.html', context) # Fixed Path

            # User is verified - set up full session data
            request.session['user_id'] = user_id
            request.session['role'] = role
            request.session['username'] = username

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
            messages.error(request, 'Invalid Username or Password.')
        else:
            messages.error(request, 'An internal error occurred. Please contact support.')

    return render(request, 'login.html') # Fixed Path

def logout_view(request):
    request.session.flush()
    if request.method == 'POST':
        from django.http import JsonResponse
        return JsonResponse({'status': 'success', 'message': 'Logged out'})
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# ============================================
# FIRST LOGIN SETUP (ACTIVATION)
# ============================================

def first_login_setup(request):
    user_id = request.session.get('pending_verification_user_id')
    # ... (rest of logic remains the same, ensure renders point to 'login.html') ...
    
    # Since first_login_setup logic is complex, I'll provide the corrected renders:
    
    if not user_id:
        if request.session.get('user_id'):
            messages.info(request, 'You have already completed setup.')
            return redirect('home')
        messages.error(request, 'Unauthorized access. Please login first.')
        return redirect('login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user. Please contact support.')
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
            success, error = otp_service.send_otp(user.mobile_number)
            if success:
                messages.success(request, 'OTP has been sent to your phone.')
                context['verification_step'] = 'otp'
            else:
                messages.error(request, f'Failed to send OTP: {error}')
                context['verification_step'] = 'start'
            return render(request, 'login.html', context) # Fixed
        
        elif action == 'verify_otp':
            otp_1 = request.POST.get('otp_1')
            otp_2 = request.POST.get('otp_2')
            otp_3 = request.POST.get('otp_3')
            otp_4 = request.POST.get('otp_4')

            if not (otp_1 and otp_2 and otp_3 and otp_4):
                messages.error(request, 'Please enter all 4 digits of the OTP.')
                context['verification_step'] = 'otp'
                return render(request, 'login.html', context) # Fixed
            
            otp_code = f"{otp_1}{otp_2}{otp_3}{otp_4}"
            success, error = otp_service.verify_otp(otp_code)
            
            if success:
                messages.success(request, 'Phone number verified successfully.')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context) # Fixed
            else:
                messages.error(request, f'Invalid OTP code: {error}')
                context['verification_step'] = 'otp'
                return render(request, 'login.html', context) # Fixed
                
        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            accept_terms = request.POST.get('accept_terms')

            if not accept_terms:
                messages.error(request, 'You must accept the Terms & Conditions.')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context) # Fixed

            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context) # Fixed
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context) # Fixed

            hashed_password = make_password(new_password)
            
            try:
                User.complete_first_login(
                    user_id=user.user_id,
                    new_password_hash=hashed_password,
                    verification_status='verified'
                )
            except Exception as e:
                messages.error(request, f'An error occurred while updating your profile: {e}')
                context['verification_step'] = 'password'
                return render(request, 'login.html', context) # Fixed
            
            request.session.pop('pending_verification_user_id', None)
            request.session.pop('pending_verification_role', None)
            
            context['verification_step'] = 'success'
            return render(request, 'login.html', context) # Fixed

    return render(request, 'login.html', context) # Fixed


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

                # 3. Initialize OTP Service
                otp_service = OTPService(request)
                
                # 4. SEND THE OTP via API (This consumes credits)
                # We use a specific template for password reset to be professional
                msg_template = "KoopTimizer Password Reset: Your verification code is {pin}. Valid for 5 minutes."
                success, error_message = otp_service.send_otp(user.mobile_number, message_template=msg_template)

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