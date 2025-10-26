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

        # Get username and password from form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Get the user's token from the form
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Build the data to send to Google for verification
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY, 
            'response': recaptcha_response
        }

        # Make the POST request to Google's server
        try:
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            r.raise_for_status()
            result = r.json()
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Server error during verification: {e}')
            return render(request, 'login.html')

        # Check if reCAPTCHA verification was successful
        if result['success']:
            # --- RECAPTCHA PASSED - PROCEED TO DATABASE LOGIN ---
            
            with connection.cursor() as cursor:
                try:
                    # Call the stored function using %s placeholders for security.
                    cursor.execute(
                        "SELECT * FROM sp_login_user(%s, %s)",
                        [username, password]
                    )
                    
                    # Fetch the single result row
                    login_result = cursor.fetchone()
                    print(f"Login result from DB: {login_result}")
                    
                    # Check if we got a result
                    if login_result is None:
                        messages.error(request, 'Invalid login attempt.')
                        return render(request, 'login.html')
                    
                    # Validate we got all expected columns
                    if len(login_result) != 5:
                        messages.error(request, 'System configuration error. Please contact support.')
                        return render(request, 'login.html')
                    
                    # Unpack the result: (status_code, user_id, role, verification_status, is_first_login)
                    status_code, user_id, role, verification_status, is_first_login = login_result
                    
                    # Validate critical fields are not None
                    if status_code is None or user_id is None or role is None:
                        messages.error(request, 'Invalid account state. Please contact support.')
                        return render(request, 'login.html')
                    
                except (OperationalError, ProgrammingError) as e:
                    # Database connection or query syntax errors
                    print(f"Database connection/query error: {e}")
                    messages.error(request, 'Unable to connect to authentication service. Please try again later.')
                    return render(request, 'login.html')
                    
                except InternalError as e:
                    # Stored procedure execution errors
                    print(f"Stored procedure error: {e}")
                    messages.error(request, 'Authentication service error. Please contact support.')
                    return render(request, 'login.html')
                    
                except Exception as e:
                    # Catch any other unexpected errors
                    print(f"Unexpected database error: {e}")
                    messages.error(request, 'An unexpected error occurred. Please try again later.')
                    return render(request, 'login.html')

            if status_code == 'SUCCESS':
                # --- Login Successful (Credentials Valid) ---

                # Set custom session variables to "log the user in"
                request.session['user_id'] = user_id
                request.session['role'] = role
                
                # Redirect to setup page if it's the first login OR if verification is pending.
                # The setup page will handle identity verification and password change.
                if is_first_login or verification_status == 'pending':
                    messages.warning(request, 'You must complete account setup: verify your identity and change your temporary password.')
                    return redirect('first_login_setup') 
                
                # --- NORMAL LOGIN ---
                else:
                    messages.success(request, f'Welcome back, {username}!')
                    # Redirect based on role
                    if role == 'admin':
                        return redirect('dashboard:admin_dashboard')
                    elif role == 'officer':
                        return redirect('dashboard:cooperative_dashboard')
                    elif role == 'staff':
                        return redirect('dashboard:staff_dashboard')
                    else:
                        messages.error(request, 'Invalid role assignment. Please contact support.')
                        return redirect('login')

            elif status_code == 'INVALID_USERNAME_OR_PASSWORD':
                # --- Login Failed (Security-safe message) ---
                messages.error(request, 'Invalid Username or Password.')
                return render(request, 'login.html')

            else: # Catches 'ERROR' or any other unexpected status_code
                messages.error(request, 'An internal error occurred. Please contact support.')
                return render(request, 'login.html')
        
        else:
            # --- RECAPTCHA FAILED ---
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'login.html')

    # This is for the GET request (just showing the page)
    return render(request, 'login.html')

def logout_view(request):
    # Clear all session data
    request.session.flush()
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


def first_login_setup(request):
    """
    Handle first-time login setup with OTP verification and password change.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please contact support.')
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_otp':
            # Send OTP via Infobip
            otp_service = OTPService()
            pin_id, success, error = otp_service.send_otp(user.phone_number)
            
            if success:
                request.session['pin_id'] = pin_id
                messages.success(request, 'OTP has been sent to your phone.')
            else:
                messages.error(request, f'Failed to send OTP: {error}')
            return render(request, 'users/first_login_setup.html', {'show_otp_form': True})

        elif action == 'verify_otp':
            pin_id = request.session.get('pin_id')
            if not pin_id:
                messages.error(request, 'OTP session expired. Please request a new OTP.')
                return render(request, 'users/first_login_setup.html')

            otp_code = request.POST.get('otp_code')
            if not otp_code:
                messages.error(request, 'Please enter the OTP code.')
                return render(request, 'users/first_login_setup.html', {'show_otp_form': True})

            otp_service = OTPService()
            success, error = otp_service.verify_otp(pin_id, otp_code)
            
            if success:
                messages.success(request, 'Phone number verified successfully.')
                return render(request, 'users/first_login_setup.html', {'show_password_form': True})
            else:
                messages.error(request, f'Invalid OTP code: {error}')
                return render(request, 'users/first_login_setup.html', {'show_otp_form': True})

        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not new_password or not confirm_password:
                messages.error(request, 'Please enter and confirm your new password.')
                return render(request, 'users/first_login_setup.html', {'show_password_form': True})

            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'users/first_login_setup.html', {'show_password_form': True})

            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'users/first_login_setup.html', {'show_password_form': True})

            # Update user password and status
            user.password = make_password(new_password)
            user.is_first_login = False
            user.verification_status = 'verified'
            user.save()

            messages.success(request, 'Your password has been updated.')

            # Redirect to role-based dashboard
            role = request.session.get('role')
            if role == 'admin':
                return redirect('dashboard:admin_dashboard')
            elif role == 'officer' or role == 'cooperative_officer':
                return redirect('dashboard:cooperative_dashboard')
            elif role == 'staff':
                return redirect('dashboard:staff_dashboard')
            return redirect('home')

    return render(request, 'users/first_login_setup.html', {'show_otp_form': False, 'show_password_form': False})