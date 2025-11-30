import json
import traceback
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden, HttpResponseServerError
from django.db import transaction, connection
from functools import wraps

# Import your models
from apps.users.models import User
from apps.account_management.models import Cooperatives
from .models import ProfileData, FinancialData, Member, Officer, Staff

# Helper decorator for session-based authentication
def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# --- HELPER FUNCTION ---
def get_cooperative_for_user(user):
    """
    Helper to find the cooperative linked to a user (via Officer or Staff).
    """
    # DEBUG: Check what we're receiving
    print(f"DEBUG get_cooperative_for_user: Received user = {user}, type = {type(user)}")
    print(f"DEBUG get_cooperative_for_user: isinstance(user, User) = {isinstance(user, User)}")
    
    # Validate input
    if not isinstance(user, User):
        print(f"DEBUG get_cooperative_for_user: ERROR - user is not a User instance! user = {user}, type = {type(user)}")
        raise ValueError(f"get_cooperative_for_user expects a User instance, got {type(user)}: {user}")
    
    # Get the user_id to use in queries (more reliable than passing the User object)
    user_id = user.user_id
    print(f"DEBUG get_cooperative_for_user: Using user_id = {user_id} for queries")
    
    # 1. Check if user is an Officer - use user_id instead of user object
    print(f"DEBUG get_cooperative_for_user: Looking up officer for user_id = {user_id}")
    try:
        officer = Officer.objects.filter(user_id=user_id).first()
        if officer:
            print(f"DEBUG get_cooperative_for_user: Found officer: {officer}, coop: {officer.coop}")
            return officer.coop
    except Exception as e:
        print(f"DEBUG get_cooperative_for_user: Error looking up officer: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Check if user is Staff - use user_id instead of user object
    print(f"DEBUG get_cooperative_for_user: Looking up staff for user_id = {user_id}")
    try:
        staff = Staff.objects.filter(user_id=user_id).first()
        if staff:
            print(f"DEBUG get_cooperative_for_user: Found staff: {staff}")
            coop = Cooperatives.objects.filter(staff=staff).first()
            print(f"DEBUG get_cooperative_for_user: Found coop: {coop}")
            return coop
    except Exception as e:
        print(f"DEBUG get_cooperative_for_user: Error looking up staff: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"DEBUG get_cooperative_for_user: No cooperative found for user")
    return None

# ==========================================
# 1. DISPLAY VIEW (GET)
# ==========================================
@login_required_custom
def profile_form_view(request):
    """
    Display the cooperative profile form.
    Only accessible to officers and staff linked to a cooperative.
    """
    user_id = request.session.get('user_id')
    
    # DEBUG: Print session info
    print(f"DEBUG profile_form_view: user_id from session = {user_id}, type = {type(user_id)}")
    print(f"DEBUG profile_form_view: Full session = {dict(request.session)}")
    
    if not user_id:
        print("DEBUG profile_form_view: No user_id in session, redirecting to login")
        return redirect('login')
    
    # Ensure we get a User instance, not a string
    user = None
    try:
        # Convert to int if it's a string representation of a number
        if isinstance(user_id, str):
            print(f"DEBUG profile_form_view: user_id is a string: '{user_id}'")
            # Try to convert to int first
            try:
                user_id_int = int(user_id)
                print(f"DEBUG profile_form_view: Converted to int: {user_id_int}")
                # If conversion succeeds, fetch by user_id
                user = User.objects.get(user_id=user_id_int)
                print(f"DEBUG profile_form_view: Found user by user_id: {user}, type: {type(user)}")
            except ValueError:
                print(f"DEBUG profile_form_view: Cannot convert to int, trying username lookup: '{user_id}'")
                # If conversion fails, it's probably a username - look it up
                user = User.objects.get(username=user_id)
                print(f"DEBUG profile_form_view: Found user by username: {user}, type: {type(user)}")
        else:
            print(f"DEBUG profile_form_view: user_id is not a string, type: {type(user_id)}, value: {user_id}")
            # user_id is already an int, get the user
            user = User.objects.get(user_id=user_id)
            print(f"DEBUG profile_form_view: Found user by user_id: {user}, type: {type(user)}")
        
        # Final validation - ensure user is actually a User instance
        print(f"DEBUG profile_form_view: Final user check - user = {user}, type = {type(user)}, isinstance = {isinstance(user, User)}")
        if not user or not isinstance(user, User):
            print(f"DEBUG profile_form_view: User validation failed! user = {user}, type = {type(user)}")
            return redirect('login')
            
    except (User.DoesNotExist, ValueError, TypeError, AttributeError) as e:
        # Log the error for debugging
        print(f"DEBUG profile_form_view: Exception fetching user: {e}, user_id type: {type(user_id)}, user_id value: {user_id}")
        import traceback
        traceback.print_exc()
        return redirect('login')

    context = {
        'profile': {},  # Use empty dict instead of None to avoid template errors
        'coop_name': 'Unknown Cooperative',
        'officers': [],
        'members': [],
        'financial_data': None,
        'coop': None  # Will be set when coop is found
    }

    # Ensure user is a User instance before calling get_cooperative_for_user
    if not isinstance(user, User):
        context['coop_name'] = "Authentication Error"
        context['error_message'] = "Invalid user session. Please log in again."
        return render(request, 'cooperatives/profile_form.html', context)

    coop = get_cooperative_for_user(user)

    if not coop:
        context['coop_name'] = "No Linked Cooperative Found"
        context['error_message'] = "You are not linked to any cooperative. Please contact an administrator."
        return render(request, 'cooperatives/profile_form.html', context)

    # Cooperative Found - Populate Context
    context['coop_name'] = coop.cooperative_name
    context['coop'] = coop  # Add coop to context for template access
    
    # Get current year and check if we should allow editing
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Year is considered ended if we're past December (month > 12 is impossible, but check if we're in a new year)
    # Actually, a year is editable until it ends (so current year is always editable)
    # Past years (year < current_year) are not editable
    
    # Get requested year from query parameter, default to current year
    requested_year = request.GET.get('year')
    if requested_year:
        try:
            requested_year = int(requested_year)
        except ValueError:
            requested_year = current_year
    else:
        requested_year = current_year
    
    # Check if the requested year is editable (only current year and future years can be edited)
    is_editable = requested_year >= current_year
    
    # Fetch Related Data - Get profile for requested year, or latest if not found
    profile_data = ProfileData.objects.filter(coop=coop, report_year=requested_year).first()
    if not profile_data:
        # If no profile for requested year, get latest profile
        profile_data = ProfileData.objects.filter(coop=coop).order_by('-report_year', '-created_at').first()
        if profile_data and profile_data.report_year:
            requested_year = profile_data.report_year
            is_editable = requested_year >= current_year
    
    # Get latest financial data for main display (matching the profile year if available)
    financial_data = FinancialData.objects.filter(coop=coop, report_year=requested_year).first()
    if not financial_data:
        financial_data = FinancialData.objects.filter(coop=coop).order_by('-report_year', '-created_at').first()
    
    # Get latest 3 years of profile records for history
    profile_history = ProfileData.objects.filter(coop=coop).order_by('-report_year', '-created_at').values(
        'profile_id', 'report_year', 'approval_status', 'created_at', 'updated_at'
    )[:3]
    
    # Get latest 3 years of financial records for history table (ordered by report_year descending)
    financial_history = FinancialData.objects.filter(coop=coop).order_by('-report_year', '-created_at').values(
        'financial_id', 'report_year', 'assets', 'paid_up_capital', 'net_surplus', 
        'approval_status', 'created_at', 'updated_at'
    )[:3]  # Limit to latest 3 years
    context['officers'] = Officer.objects.filter(coop=coop)
    # Use values() to get dictionaries instead of model instances
    # Select columns that exist in the database:
    # member_id, coop_id, fullname, gender, mobile_number, created_at
    context['members'] = list(Member.objects.filter(coop=coop).values('member_id', 'coop_id', 'fullname', 'gender', 'mobile_number', 'created_at'))
    context['financial_history'] = list(financial_history)
    context['profile_history'] = list(profile_history)
    context['current_year'] = current_year
    context['requested_year'] = requested_year
    context['is_editable'] = is_editable

    # Construct the Profile Context Dictionary
    if profile_data:
        profile_ctx = {
            'coop_name': coop.cooperative_name,
            'coop_id': coop.coop_id,
            'report_year': profile_data.report_year,
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
                'financial_attachments_exist': True if financial_data.attachments else False
            })
        
        context['profile'] = profile_ctx
    else:
        # If no profile_data, still set coop_id in profile for URL generation
        context['profile'] = {
            'coop_id': coop.coop_id if coop else None
        }

    return render(request, 'cooperatives/profile_form.html', context)


@login_required_custom
def print_profile(request, coop_id):
    """
    Renders a printable version of the cooperative profile.
    """
    try:
        user_id = request.session.get('user_id')
        
        if not user_id:
            return redirect('login')
        
        # Get user (same logic as profile_form_view)
        user = None
        try:
            if isinstance(user_id, str):
                try:
                    user_id_int = int(user_id)
                    user = User.objects.get(user_id=user_id_int)
                except ValueError:
                    user = User.objects.get(username=user_id)
            else:
                user = User.objects.get(user_id=user_id)
            
            if not user or not isinstance(user, User):
                return redirect('login')
                
        except (User.DoesNotExist, ValueError, TypeError, AttributeError):
            return redirect('login')
        
        coop = get_cooperative_for_user(user)
        
        if not coop or coop.coop_id != coop_id:
            return HttpResponseForbidden("You don't have permission to view this profile.")
        
        # Get profile data for current year or latest
        from datetime import datetime
        current_year = datetime.now().year
        
        # Get requested year from query parameter, default to current year
        requested_year = request.GET.get('year')
        if requested_year:
            try:
                requested_year = int(requested_year)
            except ValueError:
                requested_year = current_year
        else:
            requested_year = current_year
        
        profile_data = ProfileData.objects.filter(coop_id=coop_id, report_year=requested_year).first()
        if not profile_data:
            # If no profile for requested year, get latest profile
            profile_data = ProfileData.objects.filter(coop_id=coop_id).order_by('-report_year', '-created_at').first()
            if profile_data and profile_data.report_year:
                requested_year = profile_data.report_year
        
        financial_data = FinancialData.objects.filter(coop_id=coop_id, report_year=requested_year).first()
        if not financial_data:
            financial_data = FinancialData.objects.filter(coop_id=coop_id).order_by('-report_year').first()
        
        context = {
            'coop_name': coop.cooperative_name,
            'profile': {}
        }
        
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
                'cote_renewal': profile_data.cote_renewal,
                'approval_status': profile_data.approval_status,
            }
            
            # Merge Financial Data if it exists
            if financial_data:
                profile_ctx.update({
                    'assets': financial_data.assets,
                    'paid_up_capital': financial_data.paid_up_capital,
                    'net_surplus': financial_data.net_surplus,
                    'report_year': financial_data.report_year,
                })
            
            context['profile'] = profile_ctx
        
        return render(request, 'cooperatives/profile_print.html', context)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in print_profile: {str(e)}", exc_info=True)
        return HttpResponseServerError("An error occurred while generating the printable profile.")


# ==========================================
# 2. INSERT/UPDATE VIEW (POST)
# ==========================================
@login_required_custom
@require_POST
@transaction.atomic 
def create_profile(request):
    """
    Create or update a cooperative profile.
    Only accessible to officers and staff linked to a cooperative.
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        # Convert to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
                # After converting to int, fetch the user
                user = User.objects.get(user_id=user_id)
            except ValueError:
                # If it's not a number, try username lookup
                user = User.objects.get(username=user_id)
        else:
            user = User.objects.get(user_id=user_id)
        
        # Ensure user is actually a User instance
        if not isinstance(user, User):
            return JsonResponse({'success': False, 'error': 'Invalid user'}, status=401)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=401)
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid user ID'}, status=401)

    try:
        coop = get_cooperative_for_user(user)

        if not coop:
            return JsonResponse({'success': False, 'error': f'Cooperative not found for user: {user.username}'}, status=403)

        # --- Data Cleaning ---
        def clean_dec(val):
            if not val: return 0
            # Remove commas and handle empty strings
            val = str(val).replace(',', '').strip()
            try:
                return float(val) if val else 0
            except ValueError:
                return 0

        # --- File Handling ---
        coc_binary = None
        cte_binary = None
        
        if 'coc_file' in request.FILES:
            coc_file = request.FILES['coc_file']
            if coc_file.size > 10 * 1024 * 1024:  # 10MB limit
                return JsonResponse({'success': False, 'error': 'CoC file size exceeds 10MB limit'}, status=400)
            coc_binary = coc_file.read()
            
        if 'cte_file' in request.FILES:
            cte_file = request.FILES['cte_file']
            if cte_file.size > 10 * 1024 * 1024:  # 10MB limit
                return JsonResponse({'success': False, 'error': 'CTE file size exceeds 10MB limit'}, status=400)
            cte_binary = cte_file.read()

        financial_blob = None
        fin_files = request.FILES.getlist('financial_documents')
        if fin_files:
            # Check total size
            total_size = sum(f.size for f in fin_files)
            if total_size > 50 * 1024 * 1024:  # 50MB total limit
                return JsonResponse({'success': False, 'error': 'Total financial documents size exceeds 50MB limit'}, status=400)
            
            parts = []
            for f in fin_files:
                f.seek(0)
                header = f"--FILE--{f.name}--START--".encode('utf-8')
                footer = b"--END--"
                parts.append(header + f.read() + footer)
            financial_blob = b"\n".join(parts)

        # Get report_year from form or default to current year
        from datetime import datetime
        current_year = datetime.now().year
        
        report_year_str = request.POST.get('report_year')
        if report_year_str:
            try:
                report_year = int(report_year_str)
            except ValueError:
                report_year = current_year
        else:
            report_year = current_year
        
        # Check if the year is editable (prevent editing past years)
        if report_year < current_year:
            return JsonResponse({
                'success': False,
                'message': f'Cannot edit profile for year {report_year}. Only current year ({current_year}) and future years can be edited.'
            }, status=400)
        
        # --- UPDATE OR CREATE PROFILE ---
        # Use report_year in the lookup to get/create profile for specific year
        profile, created = ProfileData.objects.update_or_create(
            coop=coop,
            report_year=report_year,
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

        # Validate at least one member is provided
        valid_members = [name for name in names if name and name.strip()]
        if not valid_members:
            return JsonResponse({'success': False, 'error': 'At least one member is required'}, status=400)

        # Only delete/re-add if names were actually submitted
        if names: 
            Member.objects.filter(coop=coop).delete()
            # Use raw SQL to insert members since email column doesn't exist in DB
            # This avoids Django trying to insert the email field
            with connection.cursor() as cursor:
                for i in range(len(names)):
                    if names[i].strip():
                        # Basic validation
                        if len(names[i].strip()) < 2:
                            return JsonResponse({'success': False, 'error': f'Member name at row {i+1} is too short'}, status=400)
                        
                        fullname = names[i].strip()
                        gender_raw = genders[i] if i < len(genders) and genders[i] else None
                        # Convert gender to lowercase to match database enum values ('male', 'female', 'others')
                        gender = gender_raw.lower() if gender_raw else None
                        mobile_number = mobiles[i].strip() if i < len(mobiles) and mobiles[i] else None
                        
                        # Insert only columns that exist: coop_id, fullname, gender, mobile_number
                        # Note: email column doesn't exist, so we exclude it
                        cursor.execute("""
                            INSERT INTO members (coop_id, fullname, gender, mobile_number, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, [coop.coop_id, fullname, gender, mobile_number])

        return JsonResponse({'success': True, 'message': 'Profile saved successfully'})

    except KeyError as e:
        return JsonResponse({'success': False, 'error': f'Missing required field: {str(e)}'}, status=400)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid data format: {str(e)}'}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'An error occurred while saving the profile. Please try again.'}, status=500)

# ==========================================
# 3. DOWNLOAD VIEW
# ==========================================
@login_required_custom
def download_attachment(request, coop_id, which):
    """
    Downloads binary attachments using ORM.
    Only accessible to officers and staff linked to the cooperative.
    """
    try:
        user_id = request.session.get('user_id')
        
        if not user_id:
            return HttpResponse("Authentication required", status=401)
        
        try:
            # Convert to int if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                    # After converting to int, fetch the user
                    user = User.objects.get(user_id=user_id)
                except ValueError:
                    # If it's not a number, try username lookup
                    user = User.objects.get(username=user_id)
            else:
                user = User.objects.get(user_id=user_id)
            
            # Ensure user is actually a User instance
            if not isinstance(user, User):
                return HttpResponse("Invalid user", status=401)
        except User.DoesNotExist:
            return HttpResponse("User not found", status=401)
        except (ValueError, TypeError, AttributeError):
            return HttpResponse("Invalid user ID", status=401)
        
        # Check permissions: Ensure the logged-in user belongs to this coop
        # Use user_id for consistency and to avoid model mismatch issues
        user_id_value = user.user_id
        officer = Officer.objects.filter(user_id=user_id_value, coop_id=coop_id).first()
        staff = Staff.objects.filter(user_id=user_id_value).first()
        
        # Verify user has access to this cooperative
        if not officer and not staff:
            return HttpResponse("Access denied", status=403)
        
        # If staff, verify they have access to this cooperative
        if staff and not officer:
            coop = Cooperatives.objects.filter(staff=staff, coop_id=coop_id).first()
            if not coop:
                return HttpResponse("Access denied", status=403)
        
        filename = "download"
        file_data = None
        
        # Check if preview is requested (not download) - define early
        preview = request.GET.get('preview', '').lower() == 'true'

        if which == 'coc':
            # Get profile for specific year or latest
            year = request.GET.get('year')
            if year:
                try:
                    year_int = int(year)
                    profile = ProfileData.objects.filter(coop_id=coop_id, report_year=year_int).order_by('-created_at').first()
                except ValueError:
                    profile = None
            else:
                # Get latest profile if no year specified
                profile = ProfileData.objects.filter(coop_id=coop_id).order_by('-report_year', '-created_at').first()
            
            if not profile:
                return HttpResponse("Profile not found", status=404)
            
            file_data = profile.coc_attachment
            year_suffix = f"_{profile.report_year}" if profile.report_year else ""
            filename = f"coc_{coop_id}{year_suffix}.pdf"
            
        elif which == 'cte':
            # Get profile for specific year or latest
            year = request.GET.get('year')
            if year:
                try:
                    year_int = int(year)
                    profile = ProfileData.objects.filter(coop_id=coop_id, report_year=year_int).order_by('-created_at').first()
                except ValueError:
                    profile = None
            else:
                # Get latest profile if no year specified
                profile = ProfileData.objects.filter(coop_id=coop_id).order_by('-report_year', '-created_at').first()
            
            if not profile:
                return HttpResponse("Profile not found", status=404)
            
            file_data = profile.cote_attachment
            year_suffix = f"_{profile.report_year}" if profile.report_year else ""
            filename = f"cte_{coop_id}{year_suffix}.pdf"
            
        elif which == 'financial':
            # Get financial record - support year parameter if provided
            year = request.GET.get('year')
            if year:
                try:
                    year_int = int(year)
                    fin = FinancialData.objects.filter(coop_id=coop_id, report_year=year_int).order_by('-created_at').first()
                except ValueError:
                    fin = None
            else:
                # Get latest financial record if no year specified
                fin = FinancialData.objects.filter(coop_id=coop_id).order_by('-created_at').first()
            
            if fin:
                file_data = fin.attachments
                year_suffix = f"_{fin.report_year}" if fin.report_year else ""
                filename = f"financials_{coop_id}{year_suffix}.bin"
                
                # For preview mode, check if multiple files and handle file_index parameter
                if preview and file_data:
                    try:
                        data_bytes = bytes(file_data) if isinstance(file_data, memoryview) else file_data
                        parts = data_bytes.split(b'--FILE--')
                        file_parts = []
                        
                        for part in parts:
                            if b'--START--' in part:
                                name_end = part.find(b'--START--')
                                file_name = part[:name_end].decode('utf-8', errors='ignore')
                                content_start = name_end + len(b'--START--')
                                content_end = part.find(b'--END--', content_start)
                                if content_end > content_start:
                                    file_content = part[content_start:content_end]
                                    file_parts.append((file_name, file_content))
                        
                        # If multiple files, check for file_index parameter
                        if len(file_parts) > 1:
                            file_index = request.GET.get('file_index', '0')
                            try:
                                file_index = int(file_index)
                                if 0 <= file_index < len(file_parts):
                                    file_name, file_data = file_parts[file_index]
                                    filename = file_name
                                    # Store file count in response header for frontend
                                    # Continue with single file processing below
                            except (ValueError, IndexError):
                                # Invalid index, use first file
                                file_name, file_data = file_parts[0]
                                filename = file_name
                    except Exception as e:
                        print(f"Error parsing file list: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue with single file handling
                
                # For preview mode with financial documents, check if multiple files exist
                # If multiple files, return JSON with file list for frontend to handle
                if preview and file_data:
                    try:
                        # Parse the combined blob to extract individual files
                        file_parts = []
                        data_bytes = bytes(file_data) if isinstance(file_data, memoryview) else file_data
                        
                        # Split by file delimiters
                        parts = data_bytes.split(b'--FILE--')
                        for part in parts:
                            if b'--START--' in part:
                                name_end = part.find(b'--START--')
                                file_name = part[:name_end].decode('utf-8', errors='ignore')
                                content_start = name_end + len(b'--START--')
                                content_end = part.find(b'--END--', content_start)
                                if content_end > content_start:
                                    file_content = part[content_start:content_end]
                                    file_parts.append((file_name, file_content))
                        
                        # If multiple files found, return file list for frontend
                        if len(file_parts) > 1:
                            # Return first file for now, but indicate there are multiple
                            # Frontend will handle showing a list
                            first_file_name, first_file_content = file_parts[0]
                            file_data = first_file_content
                            filename = first_file_name
                            # Store file list in session or return as JSON
                            # For simplicity, we'll just return the first file and let frontend request others
                            # Or we can create an endpoint to get individual files
                    except Exception as e:
                        print(f"Error parsing financial documents: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fall through to single file handling
        else:
            return HttpResponseBadRequest("Invalid attachment type")

        if not file_data:
            return HttpResponse("File not found", status=404)

        # Convert memoryview to bytes if necessary
        if isinstance(file_data, memoryview):
            file_data = file_data.tobytes()
        
        # Double-check after conversion
        if file_data is None or len(file_data) == 0:
            return HttpResponse("File not found or empty", status=404)

        # preview is already defined above
        as_attachment = not preview
        
        # Determine content type
        content_type = 'application/octet-stream'
        if which == 'coc' or which == 'cte':
            content_type = 'application/pdf'  # Certificates are typically PDFs
        elif which == 'financial':
            # Try to detect content type from filename or default to PDF
            content_type = 'application/pdf'
        
        # For preview mode, try to convert files to PDF if needed
        if preview:
            from io import BytesIO
            from django.http import FileResponse
            from apps.communications.utils import convert_to_pdf, can_convert_to_pdf, decompress_pdf_gz, convert_csv_gz_to_pdf
            
            # Get file count for financial documents (before processing)
            file_count = 0
            file_index = request.GET.get('file_index', '0')
            if which == 'financial':
                try:
                    # Get original data to count files
                    fin = FinancialData.objects.filter(coop_id=coop_id, report_year=year_int if year else None).order_by('-created_at').first()
                    if fin and fin.attachments:
                        orig_data = bytes(fin.attachments) if isinstance(fin.attachments, memoryview) else fin.attachments
                        parts = orig_data.split(b'--FILE--')
                        file_count = sum(1 for part in parts if b'--START--' in part)
                except:
                    pass
            
            # Helper function to add file count headers
            def add_file_count_headers(response):
                if which == 'financial' and file_count > 1:
                    response['X-File-Count'] = str(file_count)
                    response['X-Current-File-Index'] = file_index
                return response
            
            # Check if it's a gzipped PDF
            is_pdf_gz = filename.lower().endswith('.pdf.gz')
            if is_pdf_gz:
                pdf_bytes = decompress_pdf_gz(file_data)
                if pdf_bytes:
                    stream = BytesIO(pdf_bytes)
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=filename.rsplit('.gz', 1)[0], 
                                           content_type='application/pdf')
                    response['Content-Length'] = str(len(pdf_bytes))
                    response['X-Conversion-Status'] = 'decompressed'
                    return add_file_count_headers(response)
                else:
                    # Fallback to original if decompression fails
                    stream = BytesIO(file_data)
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=filename, 
                                           content_type=content_type)
                    response['X-Conversion-Status'] = 'failed'
                    return response
            
            # Check if it's a gzipped CSV
            is_csv_gz = filename.lower().endswith('.csv.gz')
            if is_csv_gz:
                pdf_bytes = convert_csv_gz_to_pdf(file_data)
                if pdf_bytes:
                    stream = BytesIO(pdf_bytes)
                    pdf_filename = filename.rsplit('.gz', 1)[0].rsplit('.', 1)[0] + '.pdf'
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=pdf_filename, 
                                           content_type='application/pdf')
                    response['Content-Length'] = str(len(pdf_bytes))
                    response['X-Conversion-Status'] = 'converted'
                    return add_file_count_headers(response)
                else:
                    # Fallback to original if conversion fails
                    stream = BytesIO(file_data)
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=filename, 
                                           content_type=content_type)
                    response['X-Conversion-Status'] = 'failed'
                    return add_file_count_headers(response)
            
            # If already PDF, return directly
            if content_type == 'application/pdf':
                stream = BytesIO(file_data)
                response = FileResponse(stream, as_attachment=False, 
                                       filename=filename, 
                                       content_type='application/pdf')
                response['Content-Length'] = str(len(file_data))
                return add_file_count_headers(response)
            
            # Try to convert to PDF if it's a convertible type
            if can_convert_to_pdf(content_type) or filename.lower().endswith(('.docx', '.doc', '.xlsx', '.xls', '.xlsm', '.xlsb', '.pptx', '.ppt', '.txt', '.csv')):
                pdf_bytes, success = convert_to_pdf(file_data, filename, content_type)
                if success and pdf_bytes:
                    stream = BytesIO(pdf_bytes)
                    pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=pdf_filename, 
                                           content_type='application/pdf')
                    response['Content-Length'] = str(len(pdf_bytes))
                    response['X-Conversion-Status'] = 'converted'
                    return add_file_count_headers(response)
                else:
                    # If conversion fails, return original with failed status
                    stream = BytesIO(file_data)
                    response = FileResponse(stream, as_attachment=False, 
                                           filename=filename, 
                                           content_type=content_type)
                    response['X-Conversion-Status'] = 'failed'
                    return add_file_count_headers(response)
            else:
                # Not convertible, return as-is
                stream = BytesIO(file_data)
                response = FileResponse(stream, as_attachment=False, 
                                       filename=filename, 
                                       content_type=content_type)
                response['X-Conversion-Status'] = 'not_convertible'
                return add_file_count_headers(response)
        else:
            # Download mode - return file as-is
            from io import BytesIO
            from django.http import FileResponse
            stream = BytesIO(file_data)
            response = FileResponse(stream, as_attachment=True, 
                                   filename=filename, 
                                   content_type=content_type)
            response['Content-Length'] = str(len(file_data))
            return response

    except Exception as e:
        import traceback
        print(f"Download error: {e}")
        traceback.print_exc()
        return HttpResponse(f"Server error during download: {str(e)}", status=500)


@login_required_custom
def get_financial_data_by_year(request, report_year):
    """
    Get financial data for a specific report year.
    Returns JSON with financial data details.
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    
    try:
        # Convert to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
                user = User.objects.get(user_id=user_id)
            except ValueError:
                user = User.objects.get(username=user_id)
        else:
            user = User.objects.get(user_id=user_id)
        
        if not isinstance(user, User):
            return JsonResponse({'status': 'error', 'message': 'Invalid user'}, status=401)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=401)
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid user ID'}, status=401)
    
    try:
        coop = get_cooperative_for_user(user)
        
        if not coop:
            return JsonResponse({'status': 'error', 'message': 'Cooperative not found'}, status=403)
        
        # Get financial data for the specific year
        financial_data = FinancialData.objects.filter(
            coop=coop, 
            report_year=report_year
        ).order_by('-created_at').first()
        
        if not financial_data:
            return JsonResponse({
                'status': 'error', 
                'message': f'No financial data found for year {report_year}'
            }, status=404)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'financial_id': financial_data.financial_id,
                'report_year': financial_data.report_year,
                'assets': str(financial_data.assets),
                'paid_up_capital': str(financial_data.paid_up_capital),
                'net_surplus': str(financial_data.net_surplus),
                'approval_status': financial_data.approval_status,
                'has_attachments': bool(financial_data.attachments),
                'created_at': financial_data.created_at.isoformat() if financial_data.created_at else None,
                'updated_at': financial_data.updated_at.isoformat() if financial_data.updated_at else None,
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
