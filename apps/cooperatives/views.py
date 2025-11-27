import json
import traceback
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.db import transaction
from django.contrib.auth import get_user_model

# Import your models
from apps.account_management.models import Cooperatives, Staff
from .models import ProfileData, FinancialData, Member, Officer

# --- HELPER FUNCTION ---
def get_cooperative_for_user(user):
    """
    Helper to find the cooperative linked to a user (via Officer or Staff).
    """
    # 1. Check if user is an Officer
    officer = Officer.objects.filter(user=user).first()
    if officer:
        return officer.coop
    
    # 2. Check if user is Staff
    staff = Staff.objects.filter(user=user).first()
    if staff:
        return Cooperatives.objects.filter(staff=staff).first()
        
    return None

# ==========================================
# 1. DISPLAY VIEW (GET)
# ==========================================
def profile_form_view(request):
    user = request.user
    
    # Handle Anonymous User for testing
    if not user.is_authenticated:
        User = get_user_model()
        user = User.objects.first() # Force a user for testing
        print(f"DEBUG: Using Test User: {user}")

    context = {
        'profile': None,
        'coop_name': 'Unknown Cooperative',
        'officers': [],
        'members': [],
        'financial_data': None
    }

    coop = get_cooperative_for_user(user)

    if not coop:
        print("DEBUG: No Cooperative found for this user.")
        context['coop_name'] = "No Linked Cooperative Found"
        # We return early, but page still renders so you can see the error state
        return render(request, 'cooperatives/profile_form.html', context)

    # Cooperative Found - Populate Context
    context['coop_name'] = coop.cooperative_name
    
    # Fetch Related Data
    profile_data = ProfileData.objects.filter(coop=coop).first()
    financial_data = FinancialData.objects.filter(coop=coop).order_by('-created_at').first()
    context['officers'] = Officer.objects.filter(coop=coop)
    context['members'] = Member.objects.filter(coop=coop)

    # Construct the Profile Context Dictionary
    if profile_data:
        profile_ctx = {
            'coop_name': coop.cooperative_name,
            'coop_id': coop.coop_id,
            'address': profile_data.address,
            'operation_area': profile_data.operation_area,
            'mobile_number': profile_data.mobile_number,
            'email_address': profile_data.email_address,
            'cda_registration_number': profile_data.cda_registration_number,
            'cda_registration_date': profile_data.cda_registration_date,
            'lccdc_membership': profile_data.lccdc_membership,
            'lccdc_membership_date': profile_data.lccdc_membership_date,
            'business_activity': profile_data.business_activity,
            'board_of_directors_count': profile_data.board_of_directors_count,
            'salaried_employees_count': profile_data.salaried_employees_count,
            'coc_renewal': profile_data.coc_renewal,
            'coc_attachment': profile_data.coc_attachment, 
            'cote_renewal': profile_data.cote_renewal,
            'cote_attachment': profile_data.cote_attachment,
            'approval_status': profile_data.approval_status,
        }

        # Merge Financial Data into profile_ctx if it exists
        if financial_data:
            profile_ctx.update({
                'assets': financial_data.assets,
                'paid_up_capital': financial_data.paid_up_capital,
                'net_surplus': financial_data.net_surplus,
                'report_year': financial_data.report_year,
                'financial_attachments_exist': True if financial_data.attachments else False
            })
        
        context['profile'] = profile_ctx

    return render(request, 'cooperatives/profile_form.html', context)


# ==========================================
# 2. INSERT/UPDATE VIEW (POST)
# ==========================================
@require_POST
@transaction.atomic 
def create_profile(request):
    user = request.user

    # Handle Anonymous User for testing logic in POST
    if not user.is_authenticated:
        User = get_user_model()
        user = User.objects.first()

    try:
        coop = get_cooperative_for_user(user)

        if not coop:
            return JsonResponse({'success': False, 'error': f'Cooperative not found for user: {user.username}'}, status=403)

        # --- Data Cleaning ---
        def clean_dec(val):
            if not val: return 0
            # Remove commas and handle empty strings
            val = str(val).replace(',', '').strip()
            return val if val else 0

        # --- File Handling ---
        coc_binary = request.FILES['coc_file'].read() if 'coc_file' in request.FILES else None
        cte_binary = request.FILES['cte_file'].read() if 'cte_file' in request.FILES else None

        financial_blob = None
        fin_files = request.FILES.getlist('financial_documents')
        if fin_files:
            parts = []
            for f in fin_files:
                f.seek(0)
                header = f"--FILE--{f.name}--START--".encode('utf-8')
                footer = b"--END--"
                parts.append(header + f.read() + footer)
            financial_blob = b"\n".join(parts)

        # --- UPDATE OR CREATE PROFILE ---
        profile, created = ProfileData.objects.update_or_create(
            coop=coop,
            defaults={
                'address': request.POST.get('coop_address'),
                'mobile_number': request.POST.get('coop_contact'),
                'email_address': request.POST.get('coop_email'),
                'cda_registration_number': request.POST.get('cda_reg_num'),
                # Use 'or None' to handle empty strings for Dates
                'cda_registration_date': request.POST.get('cda_reg_date') or None,
                'lccdc_membership': request.POST.get('lccdc_membership') == 'yes',
                'lccdc_membership_date': request.POST.get('lccdc_membership_date') or None,
                'operation_area': request.POST.get('area_operation'),
                'business_activity': request.POST.get('business_activity'),
                'board_of_directors_count': request.POST.get('num_bod') or 0,
                'salaried_employees_count': request.POST.get('num_se') or 0,
                'coc_renewal': request.POST.get('coc') == 'yes',
                'cote_renewal': request.POST.get('cte') == 'yes',
                'approval_status': 'pending'
            }
        )

        if coc_binary:
            profile.coc_attachment = coc_binary
        if cte_binary:
            profile.cote_attachment = cte_binary
        profile.save()

        # --- UPDATE OR CREATE FINANCIALS ---
        report_year = request.POST.get('reporting_year') or None
        
        # NOTE: logic implies one financial record per year. 
        # If report_year is None, this might overwrite a record with null year.
        fin_data, created = FinancialData.objects.update_or_create(
            coop=coop,
            report_year=report_year,
            defaults={
                'assets': clean_dec(request.POST.get('assets_value')),
                'paid_up_capital': clean_dec(request.POST.get('paid_up_capital_value')),
                'net_surplus': clean_dec(request.POST.get('net_surplus_value')),
                'approval_status': 'pending'
            }
        )
        if financial_blob:
            fin_data.attachments = financial_blob
            fin_data.save()

        # --- SAVE MEMBERS ---
        names = request.POST.getlist('member_name[]')
        genders = request.POST.getlist('member_gender[]')
        mobiles = request.POST.getlist('member_mobile[]')
        emails = request.POST.getlist('member_email[]')

        # Only delete/re-add if names were actually submitted
        if names: 
            Member.objects.filter(coop=coop).delete()
            new_members = []
            for i in range(len(names)):
                if names[i].strip():
                    new_members.append(Member(
                        coop=coop,
                        fullname=names[i],
                        gender=genders[i] if i < len(genders) else None,
                        mobile_number=mobiles[i] if i < len(mobiles) else None,
                        email=emails[i] if i < len(emails) else None
                    ))
            if new_members:
                Member.objects.bulk_create(new_members)

        return JsonResponse({'success': True, 'message': 'Profile saved successfully'})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==========================================
# 3. DOWNLOAD VIEW
# ==========================================
# @login_required
def download_attachment(request, coop_id, which):
    """
    Downloads binary attachments using ORM.
    """
    try:
        # Check permissions: Ensure the logged-in user belongs to this coop
        # (Optional security step, highly recommended)
        user = request.user
        officer = Officer.objects.filter(user=user, coop_id=coop_id).first()
        staff = Staff.objects.filter(user=user).first()
        # You might need logic here to verify the staff belongs to the coop if needed
        
        filename = "download"
        file_data = None

        if which == 'coc':
            profile = get_object_or_404(ProfileData, coop_id=coop_id)
            file_data = profile.coc_attachment
            filename = f"coc_{coop_id}.pdf"
            
        elif which == 'cte':
            profile = get_object_or_404(ProfileData, coop_id=coop_id)
            file_data = profile.cote_attachment
            filename = f"cte_{coop_id}.pdf"
            
        elif which == 'financial':
            # Get latest financial record
            fin = FinancialData.objects.filter(coop_id=coop_id).order_by('-created_at').first()
            if fin:
                file_data = fin.attachments
                filename = f"financials_{coop_id}.bin"
        else:
            return HttpResponseBadRequest("Invalid attachment type")

        if not file_data:
            return HttpResponse("File not found", status=404)

        # Convert memoryview to bytes if necessary
        if isinstance(file_data, memoryview):
            file_data = file_data.tobytes()

        response = HttpResponse(file_data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        print(f"Download error: {e}")
        return HttpResponse("Server error during download", status=500)
