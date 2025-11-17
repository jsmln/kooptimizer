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
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
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

        # Call the stored procedure via User model helper
        try:
            login_result = User.login_user(username, password)
        except Exception as e:
            # Stored procedure or DB call failed — require a real login.
            messages.error(request, 'Login service unavailable. Please try again l  ater.')
            return render(request, 'login.html')

        if not login_result:
            messages.error(request, 'Invalid login attempt.')
            return render(request, 'login.html')

        status_code = login_result['status']
        user_id = login_result['user_id']
        role = login_result['role']
        verification_status = login_result['verification_status']
        is_first_login = login_result['is_first_login']

        if status_code == 'SUCCESS':
            # Set up session data
            request.session['user_id'] = user_id
            request.session['role'] = role

            # Handle first login or pending verification
            if is_first_login or verification_status == 'pending':
                messages.warning(request, 'Please complete your first-time setup.')
                return redirect('first_login_setup')

            # Redirect based on role
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

    # GET Request
    return render(request, 'login.html')

def logout_view(request):
    # Clear all session data
    request.session.flush()
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def first_login_setup(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user. Please contact support.')
        return redirect('login')

    full_mobile_number = user.mobile_number
    masked_number = ""

    if full_mobile_number and len(full_mobile_number) > 4:
        masked_number = f"{full_mobile_number[:3]}********{full_mobile_number[-2:]}"
    
    context = {
        'show_otp_form': False,
        'show_password_form': False,
        'masked_mobile_number': masked_number  
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        
        otp_service = OTPService(request)

        if action == 'send_otp':
            success, error = otp_service.send_otp(user.mobile_number)
            
            if success:
                messages.success(request, 'OTP has been sent to your phone.')
            else:
                messages.error(request, f'Failed to send OTP: {error}')
            
            context['show_otp_form'] = True
            return render(request, 'users/first_login_setup.html', context)
        
        elif action == 'verify_otp':
            otp_1 = request.POST.get('otp_1')
            otp_2 = request.POST.get('otp_2')
            otp_3 = request.POST.get('otp_3')
            otp_4 = request.POST.get('otp_4')

            # Check if all fields were filled
            if not (otp_1 and otp_2 and otp_3 and otp_4):
                messages.error(request, 'Please enter all 4 digits of the OTP.')
                context['show_otp_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            
            # Combine them into the single string your service expects
            otp_code = f"{otp_1}{otp_2}{otp_3}{otp_4}"

            otp_service = OTPService(request)
            success, error = otp_service.verify_otp(otp_code)
            
            if success:
                messages.success(request, 'Phone number verified successfully.')
                context['show_password_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            else:
                messages.error(request, f'Invalid OTP code: {error}')
                context['show_otp_form'] = True
                return render(request, 'users/first_login_setup.html', context)
        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not new_password or not confirm_password:
                messages.error(request, 'Please enter and confirm your new password.')
                context['show_password_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                context['show_password_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                context['show_password_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            # Hash the password
            hashed_password = make_password(new_password)
            
            try:
                
                User.complete_first_login(
                    user_id=user.user_id,
                    new_password_hash=hashed_password,
                    verification_status='verified'
                )
                messages.success(request, 'Your password has been updated.')

            except Exception as e:
                messages.error(request, f'An error occurred while updating your profile: {e}')
                context['show_password_form'] = True
                return render(request, 'users/first_login_setup.html', context)
            
            # Redirect to role-based dashboard
            role = request.session.get('role')
            if role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif role == 'officer':
                return redirect('dashboard:cooperative_dashboard')
            elif role == 'staff':
                return redirect('dashboard:staff_dashboard')
            return redirect('home')

    return render(request, 'users/first_login_setup.html', context)