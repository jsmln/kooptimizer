from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.template.loader import render_to_string
import json
from apps.core.services.ocr_service import optiic_service
from apps.users.models import User
from apps.account_management.models import Staff, Cooperatives, Users
from apps.cooperatives.models import ProfileData, FinancialData, Officer, Member
from django.contrib.auth.hashers import check_password

def databank_management_view(request):
    try:
        user_id = request.session.get('user_id')
        user_role = request.session.get('role')
        
        # Get filter parameter from query string (default: 'active')
        coop_filter = request.GET.get('filter', 'active')
        
        # Validate filter parameter
        if coop_filter not in ['active', 'deactivated', 'all']:
            coop_filter = 'active'
        
        if not user_id:
            return render(request, 'databank/databank_management.html', {
                'cooperatives': [],
                'deactivated_cooperatives': [],
                'profiles': [],
                'error': 'Authentication required',
                'current_filter': coop_filter
            })
        
        # Get user
        try:
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                    user = User.objects.get(user_id=user_id)
                except ValueError:
                    user = User.objects.get(username=user_id)
            else:
                user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return render(request, 'databank/databank_management.html', {
                'cooperatives': [],
                'deactivated_cooperatives': [],
                'profiles': [],
                'error': 'User not found',
                'current_filter': coop_filter
            })
        
        # Get cooperatives based on role and filter
        cooperatives = []
        deactivated_cooperatives = []
        staff_list = []
        
        with connection.cursor() as cursor:
            if user_role == 'admin':
                # Admin sees all cooperatives with staff info
                if coop_filter == 'active':
                    cursor.execute("""
                        SELECT c.*, s.fullname as staff_name, s.staff_id
                        FROM cooperatives c
                        LEFT JOIN staff s ON c.staff_id = s.staff_id
                        WHERE c.is_active IS NULL OR c.is_active = TRUE
                        ORDER BY c.cooperative_name
                    """)
                elif coop_filter == 'deactivated':
                    cursor.execute("""
                        SELECT c.*, s.fullname as staff_name, s.staff_id
                        FROM cooperatives c
                        LEFT JOIN staff s ON c.staff_id = s.staff_id
                        WHERE c.is_active = FALSE
                        ORDER BY c.cooperative_name
                    """)
                else:  # 'all'
                    cursor.execute("""
                        SELECT c.*, s.fullname as staff_name, s.staff_id
                        FROM cooperatives c
                        LEFT JOIN staff s ON c.staff_id = s.staff_id
                        ORDER BY c.cooperative_name
                    """)
            elif user_role == 'staff':
                # Staff sees only cooperatives assigned to them (active only)
                try:
                    staff = Staff.objects.get(user_id=user.user_id)
                    cursor.execute("""
                        SELECT c.*, s.fullname as staff_name, s.staff_id
                        FROM cooperatives c
                        LEFT JOIN staff s ON c.staff_id = s.staff_id
                        WHERE c.staff_id = %s AND (c.is_active IS NULL OR c.is_active = TRUE)
                        ORDER BY c.cooperative_name
                    """, [staff.staff_id])
                except Staff.DoesNotExist:
                    cursor.execute("SELECT * FROM sp_get_all_cooperatives() WHERE 1=0")  # Empty result
            else:
                # Officers don't have access to this page, but handle gracefully
                cursor.execute("SELECT * FROM sp_get_all_cooperatives() WHERE 1=0")
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                all_coops = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Separate active and deactivated for admin
                if user_role == 'admin':
                    for coop in all_coops:
                        if coop.get('is_active') is False:
                            deactivated_cooperatives.append(coop)
                        else:
                            cooperatives.append(coop)
                else:
                    cooperatives = all_coops
        
        # Get all staff for admin dropdown
        if user_role == 'admin':
            staff_list = list(Staff.objects.all().values('staff_id', 'fullname', 'user_id'))
        
        # Get profile data for bottom table
        # Admin sees all profiles, staff sees only profiles for their cooperatives
        profiles = []
        coop_ids = [c.get('coop_id') for c in cooperatives if c.get('coop_id')]
        
        if coop_ids:
            try:
                profile_queryset = ProfileData.objects.filter(coop_id__in=coop_ids).select_related('coop').order_by('-report_year', '-created_at')
                for profile in profile_queryset:
                    profiles.append({
                        'profile_id': profile.profile_id,
                        'coop_id': profile.coop_id,
                        'cooperative_name': profile.coop.cooperative_name if profile.coop else 'N/A',
                        'report_year': profile.report_year,
                        'address': profile.address,
                        'mobile_number': profile.mobile_number,
                        'email_address': profile.email_address,
                        'cda_registration_number': profile.cda_registration_number,
                        'cda_registration_date': profile.cda_registration_date,
                        'lccdc_membership': profile.lccdc_membership,
                        'lccdc_membership_date': profile.lccdc_membership_date,
                        'operation_area': profile.operation_area,
                        'business_activity': profile.business_activity,
                        'board_of_directors_count': profile.board_of_directors_count,
                        'salaried_employees_count': profile.salaried_employees_count,
                        'approval_status': profile.approval_status,
                        'created_at': profile.created_at,
                        'updated_at': profile.updated_at,
                    })
            except Exception as e:
                print(f"Error loading profiles: {e}")
                import traceback
                traceback.print_exc()

        context = {
            'cooperatives': cooperatives,
            'deactivated_cooperatives': deactivated_cooperatives,
            'profiles': profiles,
            'staff_list': staff_list,
            'user_role': user_role,
            'total_count': len(cooperatives),
            'deactivated_count': len(deactivated_cooperatives),
            'profile_count': len(profiles),
            'current_filter': coop_filter
        }
        return render(request, 'databank/databank_management.html', context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        return render(request, 'databank/databank_management.html', {
            'cooperatives': [],
            'profiles': [],
            'error': f"Database Error: {str(e)}"
        })
    

def view_attachment(request, coop_id, doc_type):
    # Placeholder for viewing attachments. 
    # You need to implement the actual file serving logic here.
    # Logic to fetch file path based on coop_id and doc_type
    # Example:
    # file_path = get_file_path(coop_id, doc_type)
    # return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    return HttpResponse("File viewing logic not implemented yet.", status=501)

@require_http_methods(["POST"])
def process_ocr(request):
    try:
        if 'image' in request.FILES:
            result = optiic_service.process_image_file(request.FILES['image'])
        elif 'url' in request.POST:
            result = optiic_service.process_image_url(request.POST.get('url'))
        elif 'base64' in request.POST:
            result = optiic_service.process_base64_image(request.POST.get('base64'))
        else:
            data = json.loads(request.body)
            if 'base64' in data:
                result = optiic_service.process_base64_image(data['base64'])
            elif 'url' in data:
                result = optiic_service.process_image_url(data['url'])
            else:
                return JsonResponse({'success': False, 'error': 'No image data'}, status=400)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def add_cooperative(request):
    try:
        user_role = request.session.get('role')
        
        # Only admin can add cooperatives
        if user_role != 'admin':
            return JsonResponse({'success': False, 'error': 'Permission denied. Only admin can add cooperatives.'}, status=403)
        
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('cooperative_name'):
            return JsonResponse({'success': False, 'error': 'Cooperative name is required'}, status=400)
        
        with connection.cursor() as cursor:
            # Insert directly into cooperatives table
            staff_id = data.get('staff_id') if data.get('staff_id') else None
            cursor.execute("""
                INSERT INTO cooperatives (staff_id, cooperative_name, category, district, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING coop_id
            """, [
                staff_id,
                data.get('cooperative_name'),
                data.get('category') or None,
                data.get('district') or None
            ])
            
            # Retrieve the new ID
            new_id = cursor.fetchone()[0]
            
        return JsonResponse({
            'success': True, 
            'coop_id': new_id, 
            'message': 'Cooperative added successfully'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_cooperative(request, coop_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_all_cooperatives()")
            columns = [col[0] for col in cursor.description]
            
            target_coop = None
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                if row_dict['coop_id'] == coop_id:
                    target_coop = row_dict
                    break
            
            if target_coop:
                return JsonResponse({'success': True, 'data': target_coop})
            else:
                return JsonResponse({'success': False, 'error': 'Cooperative not found'}, status=404)
                
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["PUT", "POST"])
def update_cooperative(request, coop_id):
    try:
        data = json.loads(request.body)
        user_role = request.session.get('role')
        
        # Check permissions
        if user_role != 'admin' and user_role != 'staff':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # If staff, verify they have access to this cooperative
        if user_role == 'staff':
            user_id = request.session.get('user_id')
            try:
                if isinstance(user_id, str):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        pass
                staff = Staff.objects.get(user_id=user_id)
                coop = Cooperatives.objects.filter(coop_id=coop_id, staff_id=staff.staff_id).first()
                if not coop:
                    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff profile not found'}, status=403)
        
        with connection.cursor() as cursor:
            # Update cooperative basic info
            staff_id = data.get('staff_id')  # For admin to assign staff
            cooperative_name = data.get('cooperative_name')
            category = data.get('category')
            district = data.get('district')
            
            # Build update query
            updates = []
            params = []
            
            if cooperative_name:
                updates.append("cooperative_name = %s")
                params.append(cooperative_name)
            if category is not None:
                updates.append("category = %s")
                params.append(category)
            if district is not None:
                updates.append("district = %s")
                params.append(district)
            if staff_id is not None and user_role == 'admin':  # Only admin can assign staff
                updates.append("staff_id = %s")
                params.append(staff_id if staff_id else None)
            
            if updates:
                params.append(coop_id)
                cursor.execute(f"""
                    UPDATE cooperatives 
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE coop_id = %s
                """, params)
            
        return JsonResponse({'success': True, 'message': 'Cooperative updated successfully'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["DELETE", "POST"])
@csrf_exempt
def delete_cooperative(request, coop_id):
    try:
        user_role = request.session.get('role')
        
        # Only admin can delete
        if user_role != 'admin':
            return JsonResponse({'success': False, 'error': 'Permission denied. Only admin can delete cooperatives.'}, status=403)
        
        # Require password in POST body
        try:
            data = json.loads(request.body)
            password = data.get('password')
        except Exception:
            password = None

        if not password:
            return JsonResponse({'success': False, 'error': 'Password is required.'}, status=400)

        # Get current user's ID from session
        current_user_id = request.session.get('user_id')
        if not current_user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated.'}, status=401)

        # Get user's password hash from database
        try:
            user = Users.objects.get(user_id=current_user_id)
            is_valid = check_password(password, user.password_hash)
        except Users.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Incorrect password.'}, status=403)
        
        with connection.cursor() as cursor:
            # Deactivate instead of delete (soft delete)
            cursor.execute("UPDATE cooperatives SET is_active = FALSE, updated_at = NOW() WHERE coop_id = %s", [coop_id])
            
        return JsonResponse({'success': True, 'message': 'Cooperative deactivated successfully'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@require_http_methods(["POST"])
@csrf_exempt
def restore_cooperative(request, coop_id):
    try:
        user_role = request.session.get('role')
        
        # Only admin can restore
        if user_role != 'admin':
            return JsonResponse({'success': False, 'error': 'Permission denied. Only admin can restore cooperatives.'}, status=403)
        
        # Require password in POST body
        try:
            data = json.loads(request.body)
            password = data.get('password')
        except Exception:
            password = None

        if not password:
            return JsonResponse({'success': False, 'error': 'Password is required.'}, status=400)

        # Get current user's ID from session
        current_user_id = request.session.get('user_id')
        if not current_user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated.'}, status=401)

        # Get user's password hash from database
        try:
            user = Users.objects.get(user_id=current_user_id)
            is_valid = check_password(password, user.password_hash)
        except Users.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        if not is_valid:
            return JsonResponse({'success': False, 'error': 'Incorrect password.'}, status=403)
        
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cooperatives SET is_active = TRUE, updated_at = NOW() WHERE coop_id = %s", [coop_id])
        return JsonResponse({'success': True, 'message': 'Cooperative restored successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def verify_password_view(request):
    """
    Verify the current user's password for sensitive operations like deactivating/reactivating cooperatives.
    """
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        if not password:
            return JsonResponse({'valid': False, 'message': 'Password is required.'}, status=400)
        
        # Get current user's ID from session
        user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({'valid': False, 'message': 'User not authenticated.'}, status=401)
        
        # Get user's password hash from database
        try:
            user = Users.objects.get(user_id=user_id)
            is_valid = check_password(password, user.password_hash)
            
            return JsonResponse({'valid': is_valid})
            
        except Users.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'User not found.'}, status=404)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'valid': False, 'message': str(e)}, status=500)

@require_http_methods(["GET"])
def get_profile_data(request):
    """Get profile data for the bottom table"""
    try:
        user_id = request.session.get('user_id')
        user_role = request.session.get('role')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        
        # Get cooperatives based on role
        coop_ids = []
        if user_role == 'admin':
            # Get all active cooperatives
            with connection.cursor() as cursor:
                cursor.execute("SELECT coop_id FROM cooperatives WHERE is_active IS NULL OR is_active = TRUE")
                coop_ids = [row[0] for row in cursor.fetchall()]
        elif user_role == 'staff':
            try:
                if isinstance(user_id, str):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        pass
                staff = Staff.objects.get(user_id=user_id)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT coop_id FROM cooperatives 
                        WHERE staff_id = %s AND (is_active IS NULL OR is_active = TRUE)
                    """, [staff.staff_id])
                    coop_ids = [row[0] for row in cursor.fetchall()]
            except Staff.DoesNotExist:
                pass
        
        if not coop_ids:
            return JsonResponse({'success': True, 'profiles': []})
        
        profiles = ProfileData.objects.filter(coop_id__in=coop_ids).select_related('coop').order_by('-report_year', '-created_at')
        
        profile_list = []
        for profile in profiles:
            profile_list.append({
                'profile_id': profile.profile_id,
                'coop_id': profile.coop_id,
                'cooperative_name': profile.coop.cooperative_name if profile.coop else 'N/A',
                'report_year': profile.report_year,
                'address': profile.address,
                'mobile_number': profile.mobile_number,
                'email_address': profile.email_address,
                'cda_registration_number': profile.cda_registration_number,
                'cda_registration_date': profile.cda_registration_date.strftime('%Y-%m-%d') if profile.cda_registration_date else None,
                'lccdc_membership': profile.lccdc_membership,
                'lccdc_membership_date': profile.lccdc_membership_date.strftime('%Y-%m-%d') if profile.lccdc_membership_date else None,
                'operation_area': profile.operation_area,
                'business_activity': profile.business_activity,
                'board_of_directors_count': profile.board_of_directors_count,
                'salaried_employees_count': profile.salaried_employees_count,
                'approval_status': profile.approval_status,
                'created_at': profile.created_at.strftime('%Y-%m-%d %H:%M:%S') if profile.created_at else None,
                'updated_at': profile.updated_at.strftime('%Y-%m-%d %H:%M:%S') if profile.updated_at else None,
            })
        
        return JsonResponse({'success': True, 'profiles': profile_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_profile_details(request, profile_id):
    """Get full profile details for modal display"""
    try:
        user_role = request.session.get('role')
        if user_role not in ['admin', 'staff']:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        profile = get_object_or_404(ProfileData, profile_id=profile_id)
        coop = profile.coop
        
        # Get financial data for the same report year
        financial_data = FinancialData.objects.filter(
            coop=coop, 
            report_year=profile.report_year
        ).first()
        
        # Get officers and members
        officers = Officer.objects.filter(coop=coop)
        members = Member.objects.filter(coop=coop)
        
        # Get financial history (latest 3 years)
        financial_history = FinancialData.objects.filter(coop=coop).order_by(
            '-report_year', '-created_at'
        ).values(
            'financial_id', 'report_year', 'assets', 'paid_up_capital', 'net_surplus',
            'approval_status', 'created_at', 'updated_at'
        )[:3]
        
        # Prepare context similar to profile_form_view
        context = {
            'profile': {
                'profile_id': profile.profile_id,  # Add profile_id for edit button
                'coop_name': coop.cooperative_name if coop else 'N/A',
                'coop_id': coop.coop_id if coop else None,
                'address': profile.address,
                'operation_area': profile.operation_area,
                'mobile_number': profile.mobile_number,
                'email_address': profile.email_address,
                'cda_registration_number': profile.cda_registration_number,
                'cda_registration_date': profile.cda_registration_date,
                'lccdc_membership': profile.lccdc_membership,
                'lccdc_membership_date': profile.lccdc_membership_date,
                'business_activity': profile.business_activity,
                'board_of_directors_count': profile.board_of_directors_count,
                'salaried_employees_count': profile.salaried_employees_count,
                'coc_renewal': profile.coc_renewal,
                'cote_renewal': profile.cote_renewal,
                'coc_attachment': profile.coc_attachment,
                'cote_attachment': profile.cote_attachment,
                'approval_status': profile.approval_status,
                'report_year': profile.report_year,
            },
            'financial': {
                'assets': financial_data.assets if financial_data else 0,
                'paid_up_capital': financial_data.paid_up_capital if financial_data else 0,
                'net_surplus': financial_data.net_surplus if financial_data else 0,
                'financial_attachments_exist': True if (financial_data and financial_data.attachments) else False,
            } if financial_data else {
                'assets': 0,
                'paid_up_capital': 0,
                'net_surplus': 0,
                'financial_attachments_exist': False,
            },
            'officers': officers,
            'members': members,
            'financial_history': financial_history,
            'current_year': profile.report_year if profile.report_year else None,
        }
        
        # Render the profile card HTML
        html = render_to_string('databank/profile_card.html', context)
        
        return JsonResponse({'success': True, 'html': html})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def approve_profile(request, profile_id):
    """Approve or cancel approval of a cooperative profile"""
    try:
        user_role = request.session.get('role')
        if user_role not in ['admin', 'staff']:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'cancel'
        
        if action not in ['approve', 'cancel']:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        profile = get_object_or_404(ProfileData, profile_id=profile_id)
        
        if action == 'approve':
            profile.approval_status = 'approved'
            profile.save()
            return JsonResponse({
                'success': True, 
                'message': 'Profile approved successfully',
                'new_status': 'approved'
            })
        elif action == 'cancel':
            # Cancel approval - set back to pending (don't change if already pending)
            if profile.approval_status == 'approved':
                profile.approval_status = 'pending'
                profile.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Approval cancelled successfully',
                    'new_status': 'pending'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Profile is not approved, cannot cancel'
                }, status=400)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_profile_for_edit(request, profile_id):
    """Get profile data in JSON format for editing"""
    try:
        user_role = request.session.get('role')
        if user_role not in ['admin', 'staff']:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        profile = get_object_or_404(ProfileData, profile_id=profile_id)
        coop = profile.coop
        
        # Get financial data
        financial_data = FinancialData.objects.filter(
            coop=coop, 
            report_year=profile.report_year
        ).first()
        
        # Get officers and members
        officers = Officer.objects.filter(coop=coop).values(
            'fullname', 'position', 'gender', 'mobile_number', 'email'
        )
        members = Member.objects.filter(coop=coop).values(
            'fullname', 'gender', 'mobile_number'
        )
        
        return JsonResponse({
            'success': True,
            'profile': {
                'coop_name': coop.cooperative_name if coop else 'N/A',
                'coop_id': coop.coop_id if coop else None,
                'address': profile.address or '',
                'operation_area': profile.operation_area or '',
                'mobile_number': profile.mobile_number or '',
                'email_address': profile.email_address or '',
                'cda_registration_number': profile.cda_registration_number or '',
                'cda_registration_date': profile.cda_registration_date.strftime('%Y-%m-%d') if profile.cda_registration_date else '',
                'lccdc_membership': profile.lccdc_membership,
                'lccdc_membership_date': profile.lccdc_membership_date.strftime('%Y-%m-%d') if profile.lccdc_membership_date else '',
                'business_activity': profile.business_activity or '',
                'board_of_directors_count': profile.board_of_directors_count or 0,
                'salaried_employees_count': profile.salaried_employees_count or 0,
                'coc_renewal': profile.coc_renewal,
                'cote_renewal': profile.cote_renewal,
                'coc_attachment_exists': bool(profile.coc_attachment),
                'cote_attachment_exists': bool(profile.cote_attachment),
                'report_year': profile.report_year or None,
            },
            'financial': {
                'assets': str(financial_data.assets) if financial_data and financial_data.assets else '0.00',
                'paid_up_capital': str(financial_data.paid_up_capital) if financial_data and financial_data.paid_up_capital else '0.00',
                'net_surplus': str(financial_data.net_surplus) if financial_data and financial_data.net_surplus else '0.00',
                'financial_attachments_exist': bool(financial_data and financial_data.attachments),
            },
            'officers': list(officers),
            'members': list(members),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def update_profile_from_databank(request, profile_id):
    """Update profile data from admin/staff in databank"""
    try:
        user_role = request.session.get('role')
        if user_role not in ['admin', 'staff']:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        profile = get_object_or_404(ProfileData, profile_id=profile_id)
        coop = profile.coop
        
        # Verify staff has access to this cooperative
        if user_role == 'staff':
            user_id = request.session.get('user_id')
            try:
                if isinstance(user_id, str):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        pass
                staff = Staff.objects.get(user_id=user_id)
                if coop.staff_id != staff.staff_id:
                    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            except Staff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Staff profile not found'}, status=403)
        
        # Data cleaning
        def clean_dec(val):
            if not val: return 0
            val = str(val).replace(',', '').strip()
            try:
                return float(val) if val else 0
            except ValueError:
                return 0
        
        # File handling
        coc_binary = None
        cte_binary = None
        remove_coc = request.POST.get('remove_coc') == 'true'
        remove_cte = request.POST.get('remove_cte') == 'true'
        
        if 'coc_file' in request.FILES:
            coc_file = request.FILES['coc_file']
            if coc_file.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'CoC file size exceeds 10MB limit'}, status=400)
            coc_binary = coc_file.read()
        elif remove_coc:
            coc_binary = b''  # Empty bytes to remove file
        
        if 'cte_file' in request.FILES:
            cte_file = request.FILES['cte_file']
            if cte_file.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'CTE file size exceeds 10MB limit'}, status=400)
            cte_binary = cte_file.read()
        elif remove_cte:
            cte_binary = b''  # Empty bytes to remove file
        
        financial_blob = None
        remove_financial = request.POST.get('remove_financial') == 'true'
        fin_files = request.FILES.getlist('financial_documents')
        if fin_files:
            total_size = sum(f.size for f in fin_files)
            if total_size > 50 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Total financial documents size exceeds 50MB limit'}, status=400)
            parts = []
            for f in fin_files:
                f.seek(0)
                header = f"--FILE--{f.name}--START--".encode('utf-8')
                footer = b"--END--"
                parts.append(header + f.read() + footer)
            financial_blob = b"\n".join(parts)
        elif remove_financial:
            financial_blob = b''  # Empty bytes to remove files
        
        # Update profile
        profile.address = request.POST.get('coop_address', profile.address)
        profile.mobile_number = request.POST.get('coop_contact', profile.mobile_number)
        profile.email_address = request.POST.get('coop_email', profile.email_address)
        profile.cda_registration_number = request.POST.get('cda_reg_num', profile.cda_registration_number)
        cda_date = request.POST.get('cda_reg_date')
        profile.cda_registration_date = cda_date if cda_date else profile.cda_registration_date
        profile.lccdc_membership = request.POST.get('lccdc_membership') == 'yes'
        lccdc_date = request.POST.get('lccdc_membership_date')
        profile.lccdc_membership_date = lccdc_date if lccdc_date else profile.lccdc_membership_date
        profile.operation_area = request.POST.get('area_operation', profile.operation_area)
        profile.business_activity = request.POST.get('business_activity', profile.business_activity)
        profile.board_of_directors_count = int(request.POST.get('num_bod', profile.board_of_directors_count or 0))
        profile.salaried_employees_count = int(request.POST.get('num_se', profile.salaried_employees_count or 0))
        profile.coc_renewal = request.POST.get('coc') == 'yes'
        profile.cote_renewal = request.POST.get('cte') == 'yes'
        
        if coc_binary is not None:
            if coc_binary == b'':
                profile.coc_attachment = None
            else:
                profile.coc_attachment = coc_binary
        if cte_binary is not None:
            if cte_binary == b'':
                profile.cote_attachment = None
            else:
                profile.cote_attachment = cte_binary
        
        profile.save()
        
        # Update financial data
        financial_data = FinancialData.objects.filter(
            coop=coop, 
            report_year=profile.report_year
        ).first()
        
        if financial_data:
            financial_data.assets = clean_dec(request.POST.get('assets_value'))
            financial_data.paid_up_capital = clean_dec(request.POST.get('paid_up_capital_value'))
            financial_data.net_surplus = clean_dec(request.POST.get('net_surplus_value'))
            if financial_blob is not None:
                if financial_blob == b'':
                    financial_data.attachments = None
                else:
                    financial_data.attachments = financial_blob
            financial_data.save()
        else:
            # Create new financial data if doesn't exist
            financial_data = FinancialData.objects.create(
                coop=coop,
                report_year=profile.report_year,
                assets=clean_dec(request.POST.get('assets_value')),
                paid_up_capital=clean_dec(request.POST.get('paid_up_capital_value')),
                net_surplus=clean_dec(request.POST.get('net_surplus_value')),
                attachments=financial_blob if financial_blob else None,
                approval_status='pending'
            )
        
        # Update members
        names = request.POST.getlist('member_name[]')
        genders = request.POST.getlist('member_gender[]')
        mobiles = request.POST.getlist('member_mobile[]')
        
        valid_members = [name for name in names if name and name.strip()]
        if not valid_members:
            return JsonResponse({'success': False, 'error': 'At least one member is required'}, status=400)
        
        if names:
            Member.objects.filter(coop=coop).delete()
            with connection.cursor() as cursor:
                for i in range(len(names)):
                    if names[i].strip():
                        if len(names[i].strip()) < 2:
                            return JsonResponse({'success': False, 'error': f'Member name at row {i+1} is too short'}, status=400)
                        fullname = names[i].strip()
                        gender_raw = genders[i] if i < len(genders) and genders[i] else None
                        gender = gender_raw.lower() if gender_raw else None
                        mobile_number = mobiles[i].strip() if i < len(mobiles) and mobiles[i] else None
                        cursor.execute("""
                            INSERT INTO members (coop_id, fullname, gender, mobile_number, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, [coop.coop_id, fullname, gender, mobile_number])
        
        return JsonResponse({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)