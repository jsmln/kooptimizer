<<<<<<< HEAD
from django.shortcuts import render
from django.http import HttpResponse

# ... (You might have other imports) ...

# ADD THIS FUNCTION
def your_message_view(request):
    # This is just a placeholder. You can build the real page here later.
    return render(request, 'communications/message.html')

# ADD THIS FUNCTION TOO
def your_announcement_view(request):
    # This is also a placeholder for the URL 'communications:announcement_form'
    return render(request, 'communications/announcement_form.html')
=======
from io import BytesIO
import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import DatabaseError, connection
from django.utils import timezone

# Import services and utils
from apps.core.services.sms_service import SmsService
from .utils import process_attachment, MAX_ATTACHMENT_SIZE

# Import your models
from .models import Cooperative, Officer, Announcement, Message, MessageRecipient
from apps.users.models import User
from apps.account_management.models import Admin, Staff
from django.db.models import Q

# ======================================================
# ANNOUNCEMENT VIEWS
# ======================================================

@csrf_exempt
@require_POST
def handle_announcement(request):
    try:
        data = json.loads(request.body)

        # --- 1. Extract data from frontend ---
        title = data.get('title')
        content = data.get('content')
        ann_type = data.get('type')  # 'sms' or 'email'
        action = data.get('action')  # 'save_draft' or 'send_sms'
        recipients = data.get('recipients', [])
        scheduled_time = data.get('scheduled_time')
        
        # --- 2. Get creator info from session ---
        creator_id = request.session.get('user_id') 
        creator_role = request.session.get('role')
        
        if not all([title, content, ann_type, action, creator_id, creator_role]):
            return JsonResponse({'status': 'error', 'message': 'Missing required data.'}, status=400)
        
        if creator_role not in ['admin', 'staff']:
             return JsonResponse({'status': 'error', 'message': 'Invalid user role.'}, status=403)
        
        # --- 3. Process recipients ---
        coop_ids = []
        officer_ids = []
        scope = 'none'

        if recipients:
            for r in recipients:
                coop_id = r.get('coop_id')
                officer_id = r.get('officer_id')
                
                if coop_id and officer_id == 'all':
                    coop_ids.append(int(coop_id))
                    if scope != 'officer': scope = 'cooperative' 
                elif coop_id and officer_id != 'all':
                    officer_ids.append(int(officer_id))
                    scope = 'officer'

        # --- 4. Determine status ---
        status = 'draft'
        if action == 'send_sms':
            status = 'sent'
        elif action == 'schedule_send':
            status = 'scheduled'
        
        # --- 5. Call Model Method to save to DB ---
        announcement_id = Announcement.save_announcement(
            title=title, content=content, ann_type=ann_type, status=status,
            scope=scope, creator_id=creator_id, creator_role=creator_role,
            coop_ids=coop_ids, officer_ids=officer_ids,
            announcement_id=data.get('announcement_id'),
            scheduled_time=scheduled_time
        )

        if not announcement_id:
             return JsonResponse({'status': 'error', 'message': 'Failed to save announcement.'}, status=500)

        # --- 6. If action is "Send", call the SMS Service ---
        if action == 'send_sms' and ann_type == 'sms':
            sms_service = SmsService()
            success, message = sms_service.send_bulk_announcement(announcement_id, content)
            
            if not success:
                return JsonResponse({'status': 'error', 'message': f"SMS API Error: {message}"}, status=500)
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Announcement successfully {status}!',
            'announcement_id': announcement_id
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {e}'}, status=500)


def announcement_view(request):
    """
    Renders the announcement form, passing all cooperative, officer,
    and announcement list data to the template.
    """
    # 1. Get Cooperatives for the dropdown
    cooperatives = Cooperative.objects.all().order_by('cooperative_name')
    cooperatives_list = [
        {'id': coop.coop_id, 'name': coop.cooperative_name}
        for coop in cooperatives
    ]

    # 2. Get Officers, grouped by coop_id
    officers = Officer.objects.select_related('coop').all().order_by('fullname')
    officers_by_coop = {}
    for officer in officers:
        if officer.coop:
            coop_id_str = str(officer.coop.coop_id) # JS keys should be strings
            if coop_id_str not in officers_by_coop:
                officers_by_coop[coop_id_str] = []
            officers_by_coop[coop_id_str].append({
                'id': officer.officer_id,
                'name': officer.fullname
            })

    # 3. Get Announcement Lists using the Model Methods
    sent_list = Announcement.get_by_status('sent')
    draft_list = Announcement.get_by_status('draft')
    scheduled_list = Announcement.get_by_status('scheduled')
    
    context = {
        'cooperatives_json': json.dumps(cooperatives_list),
        'officers_by_coop_json': json.dumps(officers_by_coop),
        'sent_announcements': sent_list,
        'draft_announcements': draft_list,
        'scheduled_announcements': scheduled_list,
    }
    
    return render(request, 'communications/announcement_form.html', context)


# ======================================================
# MESSAGES VIEWS
# ======================================================

def message_view(request):
    """
    Renders the message page.
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or not role:
        # You might want to redirect to login here instead of JSON
        return render(request, 'login.html') 
    
    context = {
        'user_id': user_id,
        'user_role': role
    }
    
    return render(request, 'communications/message.html', context)


def get_message_contacts(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or not role:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
    
    # 1. Collect all potential contacts first
    raw_contacts = []
    
    try:
        # --- ADMIN LOGIC ---
        if role == 'admin':
            officers = Officer.objects.select_related('coop', 'user').all()
            for officer in officers:
                if officer.user:
                    raw_contacts.append({
                        'user_id': officer.user.user_id,
                        'name': officer.fullname or officer.user.username,
                        'role': 'officer',
                        'avatar': (officer.fullname or officer.user.username)[0].upper(),
                        'coop': officer.coop.cooperative_name if officer.coop else "Unknown"
                    })

        # --- STAFF LOGIC (FIXED) ---
        elif role == 'staff':
            # Get Officers of assigned cooperatives
            try:
                staff_profile = Staff.objects.get(user_id=user_id)
                
                # FIX: Filter by staff_id directly to avoid "Must be Staff instance" error
                my_coops = Cooperative.objects.filter(staff_id=staff_profile.staff_id)
                
                officers = Officer.objects.filter(coop__in=my_coops).select_related('user', 'coop')
                for officer in officers:
                    if officer.user:
                        raw_contacts.append({
                            'user_id': officer.user.user_id,
                            'name': officer.fullname or officer.user.username,
                            'role': 'officer',
                            'avatar': (officer.fullname or officer.user.username)[0].upper(),
                            'coop': officer.coop.cooperative_name
                        })
            except Staff.DoesNotExist:
                print("Staff profile not found for user")
                pass

        # --- OFFICER LOGIC ---
        elif role == 'officer':
            # Get Admin
            admins = Admin.objects.select_related('user').all()
            for admin in admins:
                if admin.user:
                    raw_contacts.append({
                        'user_id': admin.user.user_id,
                        'name': admin.fullname or "Administrator",
                        'role': 'admin',
                        'avatar': 'A',
                        'coop': 'Administration'
                    })
            
            # Get Assigned Staff
            officer_profile = Officer.objects.filter(user_id=user_id).select_related('coop__staff__user').first()
            if officer_profile and officer_profile.coop and officer_profile.coop.staff and officer_profile.coop.staff.user:
                staff = officer_profile.coop.staff
                raw_contacts.append({
                    'user_id': staff.user.user_id,
                    'name': staff.fullname or staff.user.username,
                    'role': 'staff',
                    'avatar': (staff.fullname or 'S')[0].upper(),
                    'coop': 'My Coordinator'
                })

        # 2. Enrich contacts with Last Message Data & Sort
        final_contacts = []
        
        for contact in raw_contacts:
            contact_id = contact['user_id']
            
            # Query last message between current user and contact
            last_msg = Message.objects.filter(
                (Q(sender_id=user_id) & Q(messagerecipient__receiver_id=contact_id)) |
                (Q(sender_id=contact_id) & Q(messagerecipient__receiver_id=user_id))
            ).order_by('-sent_at').first()
            
            if last_msg:
                contact['last_message'] = "Attachment" if last_msg.attachment else last_msg.message
                if last_msg.sender_id == user_id:
                    contact['last_message'] = f"You: {contact['last_message']}"
                contact['last_time'] = last_msg.sent_at.isoformat()
                # Use for sorting
                contact['sort_time'] = last_msg.sent_at.timestamp()
            else:
                contact['last_message'] = ""
                contact['last_time'] = ""
                contact['sort_time'] = 0 # No messages go to bottom
            
            final_contacts.append(contact)

        # 3. Sort by time descending (newest on top)
        final_contacts.sort(key=lambda x: x['sort_time'], reverse=True)

        return JsonResponse({'status': 'success', 'contacts': final_contacts})

    except Exception as e:
        print(f"Error in get_message_contacts: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
def get_conversation(request, receiver_id):
    """
    Fetches conversation between current user and a specific receiver.
    """
    sender_id = request.session.get('user_id')
    if not sender_id:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
    
    try:
        try:
            receiver = User.objects.get(user_id=receiver_id)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Receiver not found'}, status=404)

        # --- Permission Check ---
        sender = User.objects.get(user_id=sender_id)
        allowed = False
        
        if sender.role == 'admin':
            allowed = receiver.role == 'officer' or receiver.role == 'staff'
            
        if sender.role == 'staff':
            if receiver.role == 'officer':
                try:
                    staff_profile = Staff.objects.get(user_id=sender_id)
                    receiver_officer = Officer.objects.select_related('coop').get(user_id=receiver_id)
                    if receiver_officer.coop and receiver_officer.coop.staff_id == staff_profile.staff_id:
                        allowed = True
                except (Staff.DoesNotExist, Officer.DoesNotExist):
                    allowed = False
                    
        elif sender.role == 'officer':
            if receiver.role == 'admin':
                allowed = True
            elif receiver.role == 'staff':
                try:
                    sender_officer = Officer.objects.select_related('coop__staff').get(user_id=sender_id)
                    if (sender_officer.coop and 
                        sender_officer.coop.staff and 
                        sender_officer.coop.staff.user_id == receiver_id):
                        allowed = True
                except Officer.DoesNotExist:
                    allowed = False

        if not allowed:
            return JsonResponse({'status': 'error', 'message': 'You do not have permission to view this conversation'}, status=403)

        # Call stored procedure
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_conversation(%s, %s);", [sender_id, receiver_id])
            rows = cursor.fetchall()

        message_list = []
        for row in rows:
            (msg_id, msg_sender_id, msg_receiver_id, msg_text,
             msg_attachment, msg_attachment_filename, msg_attachment_content_type, msg_attachment_size, msg_sent_at) = row
            
            is_sender = (msg_sender_id == sender_id)
            message_list.append({
                'message_id': msg_id,
                'text': msg_text,
                'type': 'outgoing' if is_sender else 'incoming',
                'time': msg_sent_at.isoformat() if hasattr(msg_sent_at, 'isoformat') else str(msg_sent_at),
                'sender_id': msg_sender_id,
                'has_attachment': bool(msg_attachment),
                'attachment_filename': msg_attachment_filename,
                'attachment_content_type': msg_attachment_content_type,
                'attachment_size': msg_attachment_size
            })

        # Get receiver display name details for header
        receiver_name = receiver.username
        try:
            if receiver.role == 'admin':
                p = Admin.objects.get(user=receiver)
                receiver_name = p.fullname or receiver.username
            elif receiver.role == 'staff':
                p = Staff.objects.get(user=receiver)
                receiver_name = p.fullname or receiver.username
            elif receiver.role == 'officer':
                p = Officer.objects.get(user=receiver)
                receiver_name = p.fullname or receiver.username
        except Exception:
            pass

        return JsonResponse({
            'status': 'success',
            'receiver_id': receiver_id,
            'receiver_name': receiver_name,
            'receiver_avatar': receiver_name[0].upper() if receiver_name else '?',
            'messages': message_list
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Receiver not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
@csrf_exempt
def send_message(request):
    """
    Sends a message from current user to a receiver.
    """
    sender_id = request.session.get('user_id')
    sender_role = request.session.get('role')
    
    if not sender_id or not sender_role:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

    if not User.objects.filter(user_id=sender_id).exists():
        request.session.flush()
        return JsonResponse({'status': 'error', 'message': 'Invalid session.'}, status=401)
    
    try:
        receiver_id = None
        message_text = ''
        files = []

        # Handle Multipart (File Uploads)
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            receiver_id = request.POST.get('receiver_id')
            message_text = request.POST.get('message', '').strip()
            # GET ALL FILES
            files = request.FILES.getlist('attachment') 
        else:
            # Handle JSON (Text only)
            data = json.loads(request.body)
            receiver_id = data.get('receiver_id')
            message_text = data.get('message', '').strip()

        if not receiver_id:
            return JsonResponse({'status': 'error', 'message': 'Missing receiver'}, status=400)

        # --- 1. Send Text Message (if exists) ---
        if message_text:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM sp_send_message(%s, %s, %s, %s, %s, %s, %s);",
                    [sender_id, receiver_id, message_text, None, None, None, None]
                )
        
        # --- 2. Send Files Individually (Loop) ---
        saved_attachments = 0
        for f in files:
            try:
                # Process attachment
                data_bytes, content_type, fname, fsize = process_attachment(f, f.name)
                
                # Send as separate message
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM sp_send_message(%s, %s, %s, %s, %s, %s, %s);",
                        [sender_id, receiver_id, "", data_bytes, fname, content_type, fsize]
                    )
                saved_attachments += 1
            except Exception as e:
                print(f"Error sending file {f.name}: {e}")

        return JsonResponse({
            'status': 'success',
            'message': 'Sent',
            'files_sent': saved_attachments
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def download_attachment(request, message_id):
    """
    Securely streams an attachment stored on a Message row.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

    try:
        try:
            msg = Message.objects.get(message_id=message_id)
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)

        if not msg.attachment:
            return JsonResponse({'status': 'error', 'message': 'No attachment for this message'}, status=404)

        # Permission: user must be sender or a recipient
        is_sender = msg.sender and getattr(msg.sender, 'user_id', None) == user_id
        is_recipient = MessageRecipient.objects.filter(message=msg, receiver__user_id=user_id).exists()

        if not (is_sender or is_recipient):
            return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

        # Stream attachment bytes
        from io import BytesIO
        data = msg.attachment
        filename = msg.attachment_filename or f"attachment_{message_id}"
        content_type = msg.attachment_content_type or 'application/octet-stream'

        # Query parameters
        thumb_flag = request.GET.get('thumb')
        download_flag = request.GET.get('download')
        format_flag = request.GET.get('format')  # 'pdf' or 'original'
        as_attachment = bool(download_flag)

        # PDF Conversion
        if format_flag == 'pdf' and content_type != 'application/pdf':
            from apps.communications.utils import convert_to_pdf
            pdf_data, success = convert_to_pdf(data, filename, content_type)
            if success:
                data = pdf_data
                filename = filename.rsplit('.', 1)[0] + '.pdf'
                content_type = 'application/pdf'
            else:
                return JsonResponse({'status': 'error', 'message': 'PDF conversion failed'}, status=400)

        # Thumbnail generation
        if thumb_flag and content_type.startswith('image'):
            try:
                img_io = BytesIO()
                from PIL import Image
                img = Image.open(BytesIO(data))
                max_dim = 480
                ratio = min(1.0, float(max_dim) / max(img.size))
                if ratio < 1.0:
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                if img.mode in ('RGBA', 'LA'):
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                img.save(img_io, format='JPEG', quality=78, optimize=True)
                img_io.seek(0)
                return FileResponse(img_io, as_attachment=False, filename=filename, content_type='image/jpeg')
            except Exception:
                pass

        stream = BytesIO(data)
        response = FileResponse(stream, as_attachment=as_attachment, filename=filename, content_type=content_type)
        try:
            if msg.attachment_size:
                response['Content-Length'] = str(len(data))
        except Exception:
            pass

        return response

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def convert_attachment_to_pdf(request, message_id):
    """
    Convert a non-PDF document to PDF on-demand.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

    try:
        try:
            msg = Message.objects.get(message_id=message_id)
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)

        if not msg.attachment:
            return JsonResponse({'status': 'error', 'message': 'No attachment for this message'}, status=404)

        is_sender = msg.sender and getattr(msg.sender, 'user_id', None) == user_id
        is_recipient = MessageRecipient.objects.filter(message=msg, receiver__user_id=user_id).exists()

        if not (is_sender or is_recipient):
            return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403)

        content_type = msg.attachment_content_type or 'application/octet-stream'
        if content_type == 'application/pdf':
            return JsonResponse({'status': 'success', 'message': 'Already PDF', 'is_pdf': True})

        from apps.communications.utils import convert_to_pdf
        filename = msg.attachment_filename or f"attachment_{message_id}"
        pdf_bytes, success = convert_to_pdf(msg.attachment, filename, content_type)

        if not success:
            return JsonResponse({'status': 'error', 'message': 'Conversion failed'}, status=400)

        stream = BytesIO(pdf_bytes)
        response = FileResponse(stream, as_attachment=False, filename=filename.rsplit('.', 1)[0] + '.pdf', content_type='application/pdf')
        response['Content-Length'] = str(len(pdf_bytes))
        return response

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
>>>>>>> 362cfd97af961fea06f50ba8610d51388bf3bdaa
