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
# from apps.core.services.email_service import EmailService
from datetime import datetime

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
def cancel_scheduled_announcement(request, announcement_id):
    """
    Cancels a scheduled announcement and reverts it to draft status.
    Only admin can cancel any scheduled announcement.
    Staff can only cancel their own.
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or role not in ['admin', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        # Get the announcement
        try:
            announcement = Announcement.objects.get(announcement_id=announcement_id)
        except Announcement.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
        
        # Check if it's actually scheduled
        if announcement.status_classification != 'scheduled':
            return JsonResponse({
                'status': 'error',
                'message': f'This announcement is {announcement.status_classification}, not scheduled.'
            }, status=400)
        
        # Permission check: Admin can cancel any, Staff can only cancel own
        if role == 'staff':
            try:
                staff_profile = Staff.objects.get(user_id=user_id)
                if announcement.staff_id != staff_profile.staff_id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'You do not have permission to cancel this scheduled announcement.'
                    }, status=403)
            except Staff.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Staff profile not found'}, status=403)
        
        # Check if it's too late (already past scheduled time)
        if announcement.sent_at and announcement.sent_at <= timezone.now():
            return JsonResponse({
                'status': 'error',
                'message': 'This announcement is past its scheduled time and may have already been sent.'
            }, status=400)
        
        # Revert to draft
        announcement.status_classification = 'draft'
        announcement.sent_at = None
        announcement.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Schedule cancelled successfully. Announcement reverted to draft.'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@csrf_exempt
@require_http_methods(["GET"])
def get_announcement_details(request, announcement_id):
    """
    Retrieves full announcement details for viewing (sent or scheduled).
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or role not in ['admin', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_announcement_details(%s);", [announcement_id])
            row = cursor.fetchone()
            
            if not row:
                return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
            
            # Parse the row data (updated to include attachments_json field)
            (ann_id, title, description, ann_type, status, scope, sent_at, created_at,
             attachment_size, attachment_filename, attachments_json,
             sender_name, sender_role, coop_recipients_json, officer_recipients_json) = row
            
            # Parse JSON strings
            import json
            coop_recipients = json.loads(coop_recipients_json) if coop_recipients_json else []
            officer_recipients = json.loads(officer_recipients_json) if officer_recipients_json else []
            attachments = json.loads(attachments_json) if attachments_json else []
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'announcement_id': ann_id,
                    'title': title,
                    'description': description,
                    'type': ann_type,
                    'status': status,
                    'scope': scope,
                    'sent_at': sent_at.isoformat() if sent_at else None,
                    'created_at': created_at.isoformat() if created_at else None,
                    # Legacy attachment support (for backward compatibility)
                    'has_attachment': (attachment_size is not None and attachment_size > 0) or len(attachments) > 0,
                    'attachment_size': int(attachment_size) if attachment_size is not None else sum(att.get('file_size', 0) for att in attachments),
                    'attachment_filename': attachment_filename,
                    # New individual attachments
                    'attachments': attachments,
                    'sender_name': sender_name,
                    'sender_role': sender_role,
                    'coop_recipients': coop_recipients,
                    'officer_recipients': officer_recipients
                }
            })
            
    except Exception as e:
        import traceback
        print(f"Error in get_announcement_details: {e}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_draft_announcement(request, announcement_id):
    """
    Retrieves a draft announcement by ID for editing.
    Admin can edit any draft (will become sender when sent).
    Staff can only edit their own drafts.
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or role not in ['admin', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        draft_data = Announcement.get_draft_by_id(announcement_id)
        
        if not draft_data:
            return JsonResponse({'status': 'error', 'message': 'Draft not found'}, status=404)
        
        # Get announcement object
        ann = Announcement.objects.get(announcement_id=announcement_id)
        
        # Permission check: Admin can edit any draft, Staff can only edit own
        if role == 'admin':
            # Admin can edit any draft - no ownership check needed
            pass
        elif role == 'staff':
            # Staff can only edit their own drafts
            try:
                staff_profile = Staff.objects.get(user_id=user_id)
                if ann.staff_id != staff_profile.staff_id:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'You do not have permission to edit this draft. Only the admin or the creator can edit drafts.'
                    }, status=403)
            except Staff.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Staff profile not found'}, status=403)
        
        return JsonResponse({
            'status': 'success',
            'data': draft_data
        })
        
    except Announcement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_draft_announcement: {error_details}")
        return JsonResponse({
            'status': 'error', 
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def handle_announcement(request):
    """
    Handles creating, updating, and sending announcements.
    Supports: save_draft, send_sms, send_email, schedule_send
    """
    try:
        # Check if it's FormData (multipart) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle FormData (with file uploads)
            data = request.POST
            title = data.get('title')
            content = data.get('content')
            ann_type = data.get('type')
            action = data.get('action')
            recipients = json.loads(data.get('recipients', '[]'))
            scheduled_time = data.get('scheduled_time')
            announcement_id = data.get('announcement_id')
            attachments = request.FILES.getlist('attachments')
        else:
            # Handle JSON (backward compatibility)
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            ann_type = data.get('type')
            action = data.get('action')
            recipients = data.get('recipients', [])
            scheduled_time = data.get('scheduled_time')
            announcement_id = data.get('announcement_id')
            attachments = []

        # --- 2. Get creator info from session ---
        creator_id = request.session.get('user_id') 
        creator_role = request.session.get('role')
        
        if not all([title, content, ann_type, action, creator_id, creator_role]):
            return JsonResponse({'status': 'error', 'message': 'Missing required data.'}, status=400)
        
        if creator_role not in ['admin', 'staff']:
             return JsonResponse({'status': 'error', 'message': 'Invalid user role.'}, status=403)
        
        # --- 3. Validate scheduled time if scheduling ---
        if action == 'schedule_send':
            if not scheduled_time:
                return JsonResponse({'status': 'error', 'message': 'Scheduled time is required.'}, status=400)
            
            try:
                # Parse the datetime string and make it timezone-aware
                scheduled_dt = datetime.fromisoformat(scheduled_time)
                # Make timezone-aware if it's naive
                if scheduled_dt.tzinfo is None:
                    scheduled_dt = timezone.make_aware(scheduled_dt)
                
                if scheduled_dt <= timezone.now():
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Scheduled time must be in the future.'
                    }, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format.'}, status=400)
        
        # --- 4. Process recipients ---
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

        # --- 5. Determine status ---
        status = 'draft'
        if action in ['send_sms', 'send_email']:
            status = 'sent'
        elif action == 'schedule_send':
            status = 'scheduled'
        
        # --- 6. Call Model Method to save to DB ---
        saved_announcement_id = Announcement.save_announcement(
            title=title, 
            content=content, 
            ann_type=ann_type, 
            status=status,
            scope=scope, 
            creator_id=creator_id, 
            creator_role=creator_role,
            coop_ids=coop_ids, 
            officer_ids=officer_ids,
            announcement_id=announcement_id,  # Pass existing ID for updates
            scheduled_time=scheduled_time
        )

        if not saved_announcement_id:
             return JsonResponse({'status': 'error', 'message': 'Failed to save announcement.'}, status=500)

        # --- 6.5. Handle attachments using new structure ---
        if ann_type == 'e-mail' and attachments:
            try:
                from .attachment_utils import save_announcement_attachments
                
                # Get user_id for tracking who uploaded
                user_id = request.session.get('user_id')
                
                # Save attachments using new structure
                success, message, count = save_announcement_attachments(
                    announcement_id=saved_announcement_id,
                    uploaded_files=attachments,
                    user_id=user_id
                )
                
                if not success:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Failed to save attachments: {message}'
                    }, status=400)
                
                print(f"Successfully saved {count} attachments for announcement {saved_announcement_id}")
                
            except Exception as e:
                print(f"Error processing attachments: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing attachments: {str(e)}'
                }, status=500)

        # --- 7. Send via appropriate service ---
        if action == 'send_sms' and ann_type == 'sms':
            sms_service = SmsService()
            success, message = sms_service.send_bulk_announcement(saved_announcement_id, content)
            
            if not success:
                return JsonResponse({'status': 'error', 'message': f"SMS API Error: {message}"}, status=500)
        
        elif action == 'send_email' and ann_type == 'e-mail':
            from apps.core.services.email_service import EmailService
            email_service = EmailService()
            success, message = email_service.send_bulk_announcement(
                saved_announcement_id, 
                content
            )
            
            if not success:
                return JsonResponse({'status': 'error', 'message': f"Email API Error: {message}"}, status=500)
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Announcement successfully {status}!',
            'announcement_id': saved_announcement_id
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
    # 1. Get Cooperatives that have at least one officer
    from django.db.models import Count
    cooperatives = Cooperative.objects.annotate(
        officer_count=Count('officer')
    ).filter(officer_count__gt=0).order_by('cooperative_name')
    
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
    
    # 4. Add recipient information to each announcement for filtering
    def add_recipients_info(announcements):
        """Add recipient names to announcements for search/filter"""
        for announcement in announcements:
            recipients_data = Announcement.get_recipients_for_announcement(announcement['announcement_id'])
            announcement['recipients_info'] = recipients_data
        return announcements
    
    sent_list = add_recipients_info(sent_list)
    draft_list = add_recipients_info(draft_list)
    scheduled_list = add_recipients_info(scheduled_list)
    
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
            
            # Count unread messages (messages sent TO me that I haven't read)
            # Use raw SQL to avoid Django ORM composite key issues
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM message_recipients mr
                    JOIN messages m ON mr.message_id = m.message_id
                    WHERE mr.receiver_id = %s 
                    AND m.sender_id = %s 
                    AND (mr.status IS NULL OR mr.status = 'sent')
                """, [user_id, contact_id])
                unread_count = cur.fetchone()[0]
            
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
            
            contact['unread_count'] = unread_count
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

        # Mark messages as read (messages sent TO me FROM the other person)
        # Use raw SQL to handle composite primary key properly
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE message_recipients mr
                SET status = 'seen', seen_at = %s
                FROM messages m
                WHERE mr.message_id = m.message_id
                AND mr.receiver_id = %s
                AND m.sender_id = %s
                AND (mr.status IS NULL OR mr.status = 'sent')
            """, [timezone.now(), sender_id, receiver_id])

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

@csrf_exempt
@require_http_methods(["GET"])
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
        
        # Handle memoryview objects from PostgreSQL bytea fields
        if isinstance(data, memoryview):
            data = bytes(data)
        elif data is None:
            return JsonResponse({'status': 'error', 'message': 'Attachment data is null'}, status=404)
            
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
        
        # Log conversion attempt
        print(f"[CONVERSION] Starting conversion for {filename} (type: {content_type})")
        
        pdf_bytes, success = convert_to_pdf(msg.attachment, filename, content_type)

        if not success or not pdf_bytes:
            print(f"[CONVERSION] Failed to convert {filename}")
            return JsonResponse({'status': 'error', 'message': 'Conversion failed. The document format may not be supported.'}, status=400)

        print(f"[CONVERSION] Successfully converted {filename} to PDF ({len(pdf_bytes)} bytes)")
        
        stream = BytesIO(pdf_bytes)
        response = FileResponse(stream, as_attachment=False, filename=filename.rsplit('.', 1)[0] + '.pdf', content_type='application/pdf')
        response['Content-Length'] = str(len(pdf_bytes))
        return response

    except Exception as e:
        print(f"[CONVERSION ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Conversion error: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def download_announcement_attachment(request, announcement_id):
    """
    Download or preview attachment from an announcement.
    Supports both new individual attachments and legacy combined attachments.
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or role not in ['admin', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
        
        # Get attachment_id from query params (for new structure)
        attachment_id = request.GET.get('attachment_id')
        
        # NEW STRUCTURE: Download specific attachment
        if attachment_id:
            try:
                from .models import AnnouncementAttachment
                attachment = AnnouncementAttachment.objects.get(
                    attachment_id=attachment_id,
                    announcement=announcement
                )
                
                data = attachment.file_data
                if isinstance(data, memoryview):
                    data = bytes(data)
                elif data is None:
                    return JsonResponse({'status': 'error', 'message': 'Attachment data is null'}, status=404)
                
                filename = attachment.original_filename
                content_type = attachment.content_type
                
                # Check if preview mode or download
                preview = request.GET.get('preview', 'false').lower() == 'true'
                format_flag = request.GET.get('format')
                
                # PDF Conversion if requested
                if format_flag == 'pdf' and content_type != 'application/pdf':
                    from apps.communications.utils import convert_to_pdf
                    pdf_data, success = convert_to_pdf(data, filename, content_type)
                    if success:
                        data = pdf_data
                        filename = filename.rsplit('.', 1)[0] + '.pdf'
                        content_type = 'application/pdf'
                    else:
                        return JsonResponse({'status': 'error', 'message': 'PDF conversion failed'}, status=400)
                
                stream = BytesIO(data)
                response = FileResponse(stream, as_attachment=not preview, filename=filename, content_type=content_type)
                response['Content-Length'] = str(len(data))
                
                return response
                
            except AnnouncementAttachment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Attachment not found'}, status=404)
        
        # LEGACY STRUCTURE: Download combined attachment
        else:
            if not announcement.attachment:
                # No legacy attachment, check if there are new attachments
                if announcement.attachments.exists():
                    # Get first attachment as default
                    first_attachment = announcement.attachments.first()
                    return JsonResponse({
                        'status': 'info',
                        'message': 'Please specify attachment_id parameter',
                        'attachment_id': first_attachment.attachment_id
                    }, status=400)
                else:
                    return JsonResponse({'status': 'error', 'message': 'No attachment found'}, status=404)
            
            # Handle legacy attachment data
            data = announcement.attachment
            
            if isinstance(data, memoryview):
                data = bytes(data)
            elif data is None:
                return JsonResponse({'status': 'error', 'message': 'Attachment data is null'}, status=404)
            
            filenames = announcement.attachment_filename.split(';') if announcement.attachment_filename else ['attachment']
            filename = filenames[0].strip() if filenames else 'attachments.bin'
            content_type = announcement.attachment_content_type or 'application/octet-stream'
            
            preview = request.GET.get('preview', 'false').lower() == 'true'
            format_flag = request.GET.get('format')
            
            if format_flag == 'pdf' and content_type != 'application/pdf':
                from apps.communications.utils import convert_to_pdf
                pdf_data, success = convert_to_pdf(data, filename, content_type)
                if success:
                    data = pdf_data
                    filename = filename.rsplit('.', 1)[0] + '.pdf'
                    content_type = 'application/pdf'
                else:
                    return JsonResponse({'status': 'error', 'message': 'PDF conversion failed'}, status=400)
            
            stream = BytesIO(data)
            response = FileResponse(stream, as_attachment=not preview, filename=filename, content_type=content_type)
            response['Content-Length'] = str(len(data))
            
            return response
        
    except Announcement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def convert_announcement_attachment_to_pdf(request, announcement_id):
    """
    Convert a specific attachment to PDF and return it.
    Supports both new individual attachments and legacy combined attachments.
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    
    if not user_id or role not in ['admin', 'staff']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
        
        # Get attachment_id from request body (for new structure)
        try:
            body = json.loads(request.body)
            attachment_id = body.get('attachment_id')
        except json.JSONDecodeError:
            attachment_id = None
        
        # NEW STRUCTURE: Convert specific attachment
        if attachment_id:
            try:
                from .models import AnnouncementAttachment
                attachment = AnnouncementAttachment.objects.get(
                    attachment_id=attachment_id,
                    announcement=announcement
                )
                
                data = attachment.file_data
                if isinstance(data, memoryview):
                    data = bytes(data)
                elif data is None:
                    return JsonResponse({'status': 'error', 'message': 'Attachment data is null'}, status=404)
                
                filename = attachment.original_filename
                content_type = attachment.content_type
                
                # Already PDF, just return it
                if content_type == 'application/pdf':
                    stream = BytesIO(data)
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=filename, 
                                           content_type='application/pdf')
                    response['Content-Length'] = str(len(data))
                    return response
                
                # Convert to PDF
                from apps.communications.utils import convert_to_pdf
                pdf_data, success = convert_to_pdf(data, filename, content_type)
                
                if not success:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Cannot convert {content_type} to PDF'
                    }, status=400)
                
                pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
                stream = BytesIO(pdf_data)
                response = FileResponse(stream, as_attachment=False, 
                                       filename=pdf_filename, 
                                       content_type='application/pdf')
                response['Content-Length'] = str(len(pdf_data))
                return response
                
            except AnnouncementAttachment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Attachment not found'}, status=404)
        
        # LEGACY STRUCTURE: Convert combined attachment
        else:
            if not announcement.attachment:
                # No legacy attachment, check if there are new attachments
                if announcement.attachments.exists():
                    first_attachment = announcement.attachments.first()
                    return JsonResponse({
                        'status': 'info',
                        'message': 'Please specify attachment_id in request body',
                        'attachment_id': first_attachment.attachment_id
                    }, status=400)
                else:
                    return JsonResponse({'status': 'error', 'message': 'No attachment found'}, status=404)
            
            # Handle legacy attachment data
            data = announcement.attachment
            
            if isinstance(data, memoryview):
                data = bytes(data)
            elif data is None:
                return JsonResponse({'status': 'error', 'message': 'Attachment data is null'}, status=404)
            
            filenames = announcement.attachment_filename.split(';') if announcement.attachment_filename else ['attachment']
            filename = filenames[0].strip() if filenames else 'attachment.bin'
            content_type = announcement.attachment_content_type or 'application/octet-stream'
            
            # Already PDF, just return it
            if content_type == 'application/pdf':
                stream = BytesIO(data)
                response = FileResponse(stream, as_attachment=False, 
                                       filename=filename, 
                                       content_type='application/pdf')
                response['Content-Disposition'] = 'inline'
                response['Content-Length'] = str(len(data))
                return response
            
            # Convert to PDF
            from apps.communications.utils import convert_to_pdf
            pdf_data, success = convert_to_pdf(data, filename, content_type)
            
            if not success:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Cannot convert {content_type} to PDF'
                }, status=400)
            
            pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
            stream = BytesIO(pdf_data)
            response = FileResponse(stream, as_attachment=False, 
                                   filename=pdf_filename, 
                                   content_type='application/pdf')
            response['Content-Length'] = str(len(pdf_data))
            return response
        
    except Announcement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)