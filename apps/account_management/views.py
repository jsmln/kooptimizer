from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import random
import string
import requests
from django.template.loader import render_to_string
from django.contrib.staticfiles.storage import staticfiles_storage

# This view renders your HTML page
def account_management(request):
    return render(request, 'account_management/account_management.html')


@csrf_exempt
def send_credentials_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            name = data.get('name')
            role = data.get('type')

            if not email or not name:
                return JsonResponse({'status': 'error', 'message': 'Email and Name are required.'}, status=400)

            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            # 4. Prepare the email content (NEW WAY)
            subject = "Your New Kooptimizer Account Credentials"

            # # Get the full, absolute URL for your logo
            # # This assumes your logo is at 'static/frontend/images/Logo.png'
            # logo_path = 'images/Header.png'
            # logo_url = request.build_absolute_uri(staticfiles_storage.url(logo_path))

            # --- HARDCODED PUBLIC URL FOR EMAIL TESTING ---
            # PASTE YOUR PUBLIC VS CODE URL HERE
            PUBLIC_TUNNEL_URL = 'https://rv9qfbq1-8000.asse.devtunnels.ms/' 

            # This builds the full public path to your image
            logo_url = f"{PUBLIC_TUNNEL_URL}/static/frontend/images/Header.png"

            # Build the context to pass to the template
            context = {
                'name': name,
                'email': email,
                'role': role,
                'temp_password': temp_password,
                'logo_url': logo_url  # Pass the logo URL to the template
            }
            
            # Render the HTML template file to a string
            html_content = render_to_string('account_management/credential_email.html', context)

            # 5. Prepare the Brevo API request (this part stays the same)
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
                'htmlContent': html_content  # <-- This is now your beautiful HTML
            }

            # 6. Send the request to Brevo
            response = requests.post(settings.BREVO_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            # 7. Return success
            return JsonResponse({
                'status': 'success',
                'message': 'Credentials sent successfully!'
            })

        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Email API Error: {e}'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)