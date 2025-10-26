# Make sure to import these at the top of your views.py
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
import requests # You may need to run 'pip install requests'

# This is an example of a login or registration view
def login_view(request):

    if request.method == 'POST':

        # Get username and password from form (adjust names as needed)
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1. Get the user's token from the form
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # 2. Build the data to send to Google for verification
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,  # Use the key from settings.py
            'response': recaptcha_response
        }

        # 3. Make the POST request to Google's server
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json() # The result is a JSON object

        # 4. Check if verification was successful
        if result['success']:
            # --- RECAPTCHA PASSED ---
            # # TODO: Add your real form logic here (e.g., create user, log them in)
            # messages.success(request, 'reCAPTCHA verified successfully!')
            # # ... continue with your code ...
            # pass # Remove this 'pass' when you add your code

            # --- A: HARDCODED LOGIN LOGIC GOES HERE ---
            HARDCODED_USERNAME = "admin"
            HARDCODED_PASSWORD = "password123" 

            print("User is human. Proceeding with login...")

            if username == HARDCODED_USERNAME and password == HARDCODED_PASSWORD:
                # Login Successful!
                messages.success(request, 'reCAPTCHA and Login verified successfully!')
                return redirect('home') # Redirect to your home URL name
            else:
                # Login Failed (Credentials Invalid)
                messages.error(request, 'Invalid Username or Password.')
                return render(request, 'login.html')

            # --- END HARDCODED LOGIN LOGIC ---
        
        else:
            # --- RECAPTCHA FAILED ---
            print("Bot detected. Stopping login.")
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'login.html') # Send them back

    # This is for the GET request (just showing the page)
    return render(request, 'login.html')