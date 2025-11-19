# account_management/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.conf import settings
import json
import random
import string
import requests
from django.template.loader import render_to_string
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import connection, DatabaseError
from django.contrib.auth.hashers import make_password
from .models import Cooperatives, Users, Admin, Staff, Officers
from django.views.decorators.http import require_http_methods
from psycopg2.extras import Json

@ensure_csrf_cookie
def account_management(request):
    staff_list = []
    officer_list = []
    admin_list = []

    with connection.cursor() as cursor:
        try:
            cursor.callproc('sp_get_all_user_accounts')
            results = cursor.fetchall()
            
            for row in results:
                user_data = {
                    'user_id': row[1],
                    'profile_id': row[2],
                    'fullname': row[3],
                    'email': row[4],
                    'contact': row[5],
                    'position': row[6],
                    'coop_name': row[7],
                    'account_type': row[8],
                }

                if row[8] == 'Staff':
                    staff_list.append(user_data)
                elif row[8] == 'Officer':
                    officer_list.append(user_data)
                elif row[8] == 'Admin':
                    admin_list.append(user_data)
        
        except DatabaseError as e:
            print(f"DatabaseError: {e}") 

    cooperatives_list = Cooperatives.objects.all()

    context = {
        'staffs': staff_list,
        'officers': officer_list,
        'admins': admin_list,
        'cooperatives': cooperatives_list,
    }
    
    return render(request, 'account_management/account_management.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def send_credentials_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            name = data.get('name')
            role = data.get('type')
            position = data.get('position')
            gender = data.get('gender')
            contact = data.get('contact')

            officer_coop_id = None
            staff_coop_ids = None
            coop_name_for_email = "N/A"
            
            if role == 'officer':
                officer_coop_id = data.get('coop')
                if not officer_coop_id:
                     return JsonResponse({'status': 'error', 'message': 'Cooperative is required for officers.'}, status=400)
                coop_name_for_email = Cooperatives.objects.get(pk=officer_coop_id).cooperative_name
            elif role == 'staff':
                staff_coop_ids = data.get('coop', [])
                if staff_coop_ids:
                    coop_names = Cooperatives.objects.filter(pk__in=staff_coop_ids).values_list('cooperative_name', flat=True)
                    coop_name_for_email = ", ".join(coop_names)
                else:
                    coop_name_for_email = "N/A"

            if not email or not name or not role:
                return JsonResponse({'status': 'error', 'message': 'Email, Name, and Role are required.'}, status=400)

            # Generate temporary password
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            password_hash = make_password(temp_password)

            # Create user in database
            new_user_data = {}
            with connection.cursor() as cursor:
                # Call the stored procedure directly with proper casting for all parameters
                cursor.execute("""
                    SELECT * FROM sp_create_user_profile(
                        %s::varchar,           -- p_username
                        %s::varchar,           -- p_password_hash
                        %s::user_role_enum,    -- p_role
                        %s::varchar,           -- p_fullname
                        %s::varchar,           -- p_email
                        %s::varchar,           -- p_mobile_number
                        %s::gender_enum,       -- p_gender
                        %s::varchar,           -- p_position
                        %s::integer,           -- p_officer_coop_id
                        %s::integer[]          -- p_staff_coop_ids
                    )
                """, [
                    email,           # p_username
                    password_hash,   # p_password_hash
                    role,            # p_role
                    name,            # p_fullname
                    email,           # p_email
                    contact,         # p_mobile_number
                    gender,          # p_gender
                    position,        # p_position
                    officer_coop_id, # p_officer_coop_id
                    staff_coop_ids   # p_staff_coop_ids
                ])
                result = cursor.fetchone()
                new_user_data = {
                    'user_id': result[0],
                    'profile_id': result[1],
                    'formatted_id': result[2],
                    'role': result[3],
                    'name': name,
                    'email': email,
                    'contact': contact,
                    'position': position,
                    'coop_name': coop_name_for_email
                }

            # Send email via Brevo
            try:
                subject = "Your New Kooptimizer Account Credentials"
                PUBLIC_TUNNEL_URL = 'https://rv9qfbq1-8000.asse.devtunnels.ms/'
                logo_url = f"{PUBLIC_TUNNEL_URL}/static/frontend/images/header.png"
                
                context = {
                    'name': name,
                    'email': email,
                    'role': role.capitalize(),
                    'temp_password': temp_password,
                    'logo_url': logo_url
                }
                
                html_content = render_to_string('account_management/credential_email.html', context)
                
                # Brevo API payload - EXACT format from working code
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
                
                print("=" * 80)
                print("BREVO EMAIL REQUEST")
                print(f"API URL: {settings.BREVO_API_URL}")
                print(f"Sender: {settings.BREVO_SENDER_NAME} <{settings.BREVO_SENDER_EMAIL}>")
                print(f"Recipient: {name} <{email}>")
                print(f"Subject: {subject}")
                print("=" * 80)
                
                # Use requests.post with json parameter (auto-converts to JSON)
                response = requests.post(
                    settings.BREVO_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"Response Status: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text}")
                print("=" * 80)
                
                # Brevo returns 201 on success
                if response.status_code in [200, 201]:
                    print("✓ Email sent successfully!")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Credentials sent successfully!',
                        'user': new_user_data
                    })
                else:
                    # Parse error response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', response.text)
                    except:
                        error_msg = response.text
                    
                    print(f"✗ Brevo API Error: {error_msg}")
                    raise Exception(f"Brevo API Error ({response.status_code}): {error_msg}")
                
            except Exception as e:
                print(f"✗ Email Error: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Rollback user creation on email failure
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM users WHERE user_id = %s", [new_user_data['user_id']])
                    print(f"✓ Rolled back user creation for user_id: {new_user_data['user_id']}")
                except Exception as rollback_error:
                    print(f"✗ Rollback error: {rollback_error}")
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to send credentials. Error: {str(e)}'
                }, status=500)

        except Exception as e:
            print(f"General Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def get_user_details_view(request, user_id):
    try:
        with connection.cursor() as cursor:
            cursor.callproc('sp_get_user_details', [user_id])
            details = cursor.fetchone()[0]
            if details:
                return JsonResponse({'status': 'success', 'details': details})
            else:
                return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
    except Exception as e:
        print(f"Error getting user details: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_user_view(request, user_id):
    try:
        data = json.loads(request.body)
        role = data.get('type')
        
        officer_coop_id = None
        staff_coop_ids = None
        
        if role == 'officer':
            officer_coop_id = data.get('coop')
        elif role == 'staff':
            staff_coop_ids = data.get('coop', [])

        with connection.cursor() as cursor:
            cursor.callproc('sp_update_user_profile', [
                user_id,
                data.get('name'),
                data.get('email'),
                data.get('contact'),
                data.get('gender'),
                data.get('position'),
                officer_coop_id,
                staff_coop_ids
            ])
        
        return JsonResponse({'status': 'success', 'message': 'User updated successfully.'})
    except Exception as e:
        print(f"Error updating user: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def deactivate_user_view(request, user_id):
    try:
        with connection.cursor() as cursor:
            cursor.callproc('sp_deactivate_user', [user_id])
        
        return JsonResponse({'status': 'success', 'message': 'User deactivated successfully.'})
    except Exception as e:
        print(f"Error deactivating user: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)