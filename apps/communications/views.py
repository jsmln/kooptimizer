# In your views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import DatabaseError # Import this
from apps.core.services.sms_service import SmsService
import json

# Import your models
from .models import Cooperative, Officer, Announcement

@csrf_exempt # Use CSRF token in production
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
        
        # --- 3. Process recipients (Unchanged) ---
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

        # --- 4. Determine status (Unchanged) ---
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

        # --- 6. If action is "Send", call the SMS Service (Unchanged) ---
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


def message_view(request):
    # This is just a placeholder.
    return render(request, 'communications/message.html')


def announcement_view(request):
    """
    Renders the announcement form, passing all cooperative, officer,
    and announcement list data to the template.
    """
    
    # 1. Get Cooperatives for the dropdown (Unchanged)
    cooperatives = Cooperative.objects.all().order_by('cooperative_name')
    cooperatives_list = [
        {'id': coop.coop_id, 'name': coop.cooperative_name}
        for coop in cooperatives
    ]

    # 2. Get Officers, grouped by coop_id (Unchanged)
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

    # 3. Get Announcement Lists using the new Model Methods
    sent_list = Announcement.get_by_status('sent')
    draft_list = Announcement.get_by_status('draft')
    scheduled_list = Announcement.get_by_status('scheduled')
    
    context = {
        # Data for dropdowns
        'cooperatives_json': json.dumps(cooperatives_list),
        'officers_by_coop_json': json.dumps(officers_by_coop),
        
        # Data for sidebar lists
        'sent_announcements': sent_list,
        'draft_announcements': draft_list,
        'scheduled_announcements': scheduled_list,
    }
    
    return render(request, 'communications/announcement_form.html', context)
# ADD THIS FUNCTION
def your_message_view(request):
    # This is just a placeholder. You can build the real page here later.
    return render(request, 'communications/message.html')