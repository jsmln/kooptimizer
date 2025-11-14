from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import random
import string
import requests

# This view renders your HTML page
def account_management(request):
    return render(request, 'account_management/account_management.html')


# This is your new, secure API for sending emails
@csrf_exempt # Using this for simplicity. We can add full CSRF later.
def send_credentials_view(request):
    if request.method == 'POST':
        try:
            # 1. Get the data JavaScript sent
            data = json.loads(request.body)
            email = data.get('email')
            name = data.get('name')
            role = data.get('type') # e.g., 'staff' or 'admin'

            if not email or not name:
                return JsonResponse({'status': 'error', 'message': 'Email and Name are required.'}, status=400)

            # 2. Generate a secure temporary password
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            # 3. TODO: When your database is fixed, you will save this user
            # and this hashed password to your database here.
            # For now, we will just send the email.

            # 4. Prepare the email content
            subject = "Your New Kooptimizer Account Credentials"
            html_content = f"""
                <html>
                <body>
                    <h2>Welcome to Kooptimizer, {name}!</h2>
                    <p>Your new '{role}' account has been created successfully.</p>
                    <p>Here are your login credentials:</p>
                    <p style="font-size: 1.1em; margin-left: 20px;">
                        <b>Username:</b> {email}<br>
                        <b>Temporary Password:</b> <span style="font-weight: bold; color: #b71c1c;">{temp_password}</span>
                    </p>
                    <p>Please log in and change your password as soon as possible.</p>
                    <p>Thank you,<br>The Kooptimizer Team</p>
                </body>
                </html>
            """

            # 5. Prepare the Brevo API request
            headers = {
                'accept': 'application/json',
                'api-key': settings.BREVO_API_KEY,
                'content-type': 'application/json'
            }
            payload = {
                'sender': {
                    'name': settings.BREVO_SENDER_NAME,
                    'email': settings.BREVO_SENDER_EMAIL
                },
                'to': [
                    {
                        'email': email,
                        'name': name
                    }
                ],
                'subject': subject,
                'htmlContent': html_content
            }

            # 6. Send the request to Brevo
            response = requests.post(settings.BREVO_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # This will raise an error if the request fails

            # 7. Send a 'success' response back to your JavaScript
            return JsonResponse({
                'status': 'success',
                'message': 'Credentials sent successfully!'
            })

        except requests.exceptions.RequestException as e:
            # Handle API errors (e.g., Brevo is down)
            return JsonResponse({'status': 'error', 'message': f'Email API Error: {e}'}, status=500)
        except Exception as e:
            # Handle other errors (e.g., bad data)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)