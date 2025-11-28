from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q, Avg, Max, Min
from django.db import connection
from functools import wraps
from decimal import Decimal
from datetime import datetime, timedelta
import json

from apps.account_management.models import Users, Staff as AccountStaff, Cooperatives, Officers, Admin
from apps.cooperatives.models import ProfileData, FinancialData, Member, Staff as CoopStaff, Officer
from apps.users.models import User

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = request.session.get('role')
            if user_role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def get_user_cooperatives(user_id, role):
    """Helper function to get cooperatives accessible by user based on role"""
    if role == 'admin':
        return Cooperatives.objects.all()
    elif role == 'staff':
        try:
            staff = AccountStaff.objects.get(user_id=user_id)
            return Cooperatives.objects.filter(staff=staff)
        except AccountStaff.DoesNotExist:
            return Cooperatives.objects.none()
    elif role == 'officer':
        try:
            officer = Officers.objects.filter(user_id=user_id).first()
            if officer:
                return Cooperatives.objects.filter(coop_id=officer.coop_id)
            return Cooperatives.objects.none()
        except:
            return Cooperatives.objects.none()
    return Cooperatives.objects.none()

@login_required
@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html', {
        'page_title': 'Admin Dashboard'
    })

@login_required
@role_required(['officer'])
def cooperative_dashboard(request):
    user_id = request.session.get('user_id')
    cooperative = None
    try:
        officer = Officers.objects.filter(user_id=user_id).first()
        if officer:
            cooperative = officer.coop
    except:
        pass
    
    return render(request, 'dashboard/cooperative_dashboard.html', {
        'page_title': 'Cooperative Dashboard',
        'cooperative': cooperative
    })

@login_required
@role_required(['staff'])
def staff_dashboard(request):
    return render(request, 'dashboard/staff_dashboard.html', {
        'page_title': 'Staff Dashboard'
    })

# API Endpoints for Dashboard Data
@login_required
def dashboard_stats_api(request):
    """Get dashboard statistics based on user role"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        # Basic counts
        total_coops = user_coops.count()
        total_members = Member.objects.filter(coop__coop_id__in=coop_ids).count() if coop_ids else 0
        total_officers = Officers.objects.filter(coop_id__in=coop_ids).count() if coop_ids else 0
        
        # Financial totals (latest year for each coop)
        total_assets = 0
        if coop_ids:
            financial_data = FinancialData.objects.filter(coop__coop_id__in=coop_ids)
            # Get latest financial data per cooperative
            for coop_id in coop_ids:
                latest = financial_data.filter(coop__coop_id=coop_id).order_by('-report_year').first()
                if latest:
                    total_assets += float(latest.assets)
        
        # User counts (role-based)
        if role == 'admin':
            total_admins = Admin.objects.count()
            total_staff = AccountStaff.objects.count()
            pending_users = Users.objects.filter(verification_status='pending').count()
        else:
            total_admins = 0
            total_staff = 0
            pending_users = 0
        
        # LCCDC members
        lccdc_members = ProfileData.objects.filter(
            coop__coop_id__in=coop_ids,
            lccdc_membership=True
        ).values('coop').distinct().count() if coop_ids else 0
        
        return JsonResponse({
            'total_cooperatives': total_coops,
            'total_members': total_members,
            'total_officers': total_officers,
            'total_assets': round(total_assets, 2),
            'total_admins': total_admins,
            'total_staff': total_staff,
            'pending_users': pending_users,
            'lccdc_members': lccdc_members
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_charts_api(request):
    """Get chart data based on user role"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        # Business Activity Distribution
        business_activities = {}
        if coop_ids:
            profiles = ProfileData.objects.filter(coop__coop_id__in=coop_ids).values('business_activity').annotate(count=Count('coop', distinct=True))
            for p in profiles:
                activity = p['business_activity'] or 'Not Specified'
                business_activities[activity] = p['count']
        
        # Category Distribution
        categories = {}
        if coop_ids:
            category_data = user_coops.values('category').annotate(count=Count('coop_id'))
            for c in category_data:
                cat = c['category'] or 'Not Specified'
                categories[cat] = c['count']
        
        # District Distribution
        districts = {}
        if coop_ids:
            district_data = user_coops.values('district').annotate(count=Count('coop_id'))
            for d in district_data:
                dist = d['district'] or 'Not Specified'
                districts[dist] = d['count']
        
        # Compliance Status
        compliance_data = {'coc': {'active': 0, 'inactive': 0}, 'cote': {'active': 0, 'inactive': 0}}
        if coop_ids:
            profiles = ProfileData.objects.filter(coop__coop_id__in=coop_ids)
            for profile in profiles:
                if profile.coc_renewal:
                    compliance_data['coc']['active'] += 1
                else:
                    compliance_data['coc']['inactive'] += 1
                if profile.cote_renewal:
                    compliance_data['cote']['active'] += 1
                else:
                    compliance_data['cote']['inactive'] += 1
        
        # Financial Trend (last 5 years) - separate metrics
        financial_trend = {'assets': {}, 'capital': {}, 'surplus': {}}
        if coop_ids:
            current_year = datetime.now().year
            for year in range(current_year - 4, current_year + 1):
                year_data = FinancialData.objects.filter(
                    coop__coop_id__in=coop_ids,
                    report_year=year
                ).aggregate(
                    total_assets=Sum('assets'),
                    total_capital=Sum('paid_up_capital'),
                    total_surplus=Sum('net_surplus')
                )
                financial_trend['assets'][str(year)] = float(year_data['total_assets'] or 0)
                financial_trend['capital'][str(year)] = float(year_data['total_capital'] or 0)
                financial_trend['surplus'][str(year)] = float(year_data['total_surplus'] or 0)
        
        # Top Cooperatives by Assets
        top_coops = []
        if coop_ids:
            coop_assets = []
            for coop_id in coop_ids:
                latest = FinancialData.objects.filter(coop__coop_id=coop_id).order_by('-report_year').first()
                if latest:
                    coop = user_coops.filter(coop_id=coop_id).first()
                    if coop:
                        coop_assets.append({
                            'name': coop.cooperative_name,
                            'assets': float(latest.assets)
                        })
            
            top_coops = sorted(coop_assets, key=lambda x: x['assets'], reverse=True)[:20]
        
        return JsonResponse({
            'business_activities': business_activities,
            'categories': categories,
            'districts': districts,
            'compliance': compliance_data,
            'financial_trend': financial_trend,
            'top_cooperatives': top_coops
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_cooperatives_list_api(request):
    """Get list of cooperatives with filters"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        
        cooperatives = []
        for coop in user_coops:
            # Get latest profile
            latest_profile = ProfileData.objects.filter(coop__coop_id=coop.coop_id).order_by('-report_year').first()
            latest_financial = FinancialData.objects.filter(coop__coop_id=coop.coop_id).order_by('-report_year').first()
            
            cooperatives.append({
                'coop_id': coop.coop_id,
                'name': coop.cooperative_name,
                'category': coop.category or 'Not Specified',
                'district': coop.district or 'Not Specified',
                'address': latest_profile.address if latest_profile else None,
                'email': latest_profile.email_address if latest_profile else None,
                'cda_number': latest_profile.cda_registration_number if latest_profile else None,
                'approval_status': latest_financial.approval_status if latest_financial else 'pending'
            })
        
        return JsonResponse({'cooperatives': cooperatives})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_staff_workload_api(request):
    """Get staff workload data (admin only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        staff_list = []
        all_staff = AccountStaff.objects.all()
        
        for staff in all_staff:
            assigned_coops = Cooperatives.objects.filter(staff=staff).count()
            
            # Determine workload status
            if assigned_coops >= 15:
                status = 'Heavy'
                badge_class = 'danger'
            elif assigned_coops >= 8:
                status = 'Moderate'
                badge_class = 'warning'
            else:
                status = 'Balanced'
                badge_class = 'success'
            
            staff_list.append({
                'staff_id': staff.staff_id,
                'name': staff.fullname or staff.user.username,
                'assigned_count': assigned_coops,
                'status': status,
                'badge_class': badge_class
            })
        
        return JsonResponse({'staff_workload': staff_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_pending_reviews_api(request):
    """Get pending reviews (admin/staff only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        pending_reviews = []
        if coop_ids:
            # Get financial data with pending approval
            pending_financial = FinancialData.objects.filter(
                coop__coop_id__in=coop_ids,
                approval_status='pending'
            ).order_by('-created_at')[:10]
            
            for fin in pending_financial:
                coop = user_coops.filter(coop_id=fin.coop.coop_id).first()
                if coop:
                    pending_reviews.append({
                        'coop_name': coop.cooperative_name,
                        'year': fin.report_year,
                        'assets': float(fin.assets),
                        'type': 'Financial Report'
                    })
        
        return JsonResponse({'pending_reviews': pending_reviews})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_recent_activity_api(request):
    """Get recent activity timeline"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        activities = []
        if coop_ids:
            # Recent profile updates
            recent_profiles = ProfileData.objects.filter(
                coop__coop_id__in=coop_ids
            ).order_by('-updated_at')[:5]
            
            for profile in recent_profiles:
                coop = user_coops.filter(coop_id=profile.coop.coop_id).first()
                if coop:
                    activities.append({
                        'type': 'profile_update',
                        'icon': 'pencil-square',
                        'color': 'red',
                        'title': 'Profile Updated',
                        'description': f'{coop.cooperative_name} updated profile for year {profile.report_year}',
                        'time': profile.updated_at.isoformat() if profile.updated_at else None
                    })
            
            # Recent financial updates
            recent_financial = FinancialData.objects.filter(
                coop__coop_id__in=coop_ids
            ).order_by('-updated_at')[:5]
            
            for fin in recent_financial:
                coop = user_coops.filter(coop_id=fin.coop.coop_id).first()
                if coop:
                    activities.append({
                        'type': 'financial_update',
                        'icon': 'file-earmark-text',
                        'color': 'blue',
                        'title': 'Financial Report Uploaded',
                        'description': f'{coop.cooperative_name} uploaded {fin.report_year} financial report',
                        'time': fin.updated_at.isoformat() if fin.updated_at else None
                    })
        
        # Sort by time and get most recent
        activities.sort(key=lambda x: x['time'] if x['time'] else '', reverse=True)
        activities = activities[:10]
        
        return JsonResponse({'activities': activities})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_member_demographics_api(request):
    """Get member demographics (gender breakdown)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        demographics = {'male': 0, 'female': 0, 'others': 0, 'total': 0}
        
        if coop_ids:
            members = Member.objects.filter(coop__coop_id__in=coop_ids)
            for member in members:
                demographics['total'] += 1
                gender = (member.gender or '').lower()
                if gender == 'male':
                    demographics['male'] += 1
                elif gender == 'female':
                    demographics['female'] += 1
                else:
                    demographics['others'] += 1
        
        return JsonResponse(demographics)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_user_traffic_api(request):
    """Get user traffic data for the last 30 days"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Get last 30 days
        from datetime import datetime, timedelta
        today = datetime.now().date()
        dates = []
        traffic_data = []
        
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            dates.append(date.strftime('%b %d'))
            
            # Count users who were active on this date
            # Using created_at as proxy for activity (you can enhance this with actual login tracking)
            count = Users.objects.filter(
                created_at__date=date
            ).count()
            
            # Also count users who logged in recently (if you have last_active tracking)
            recent_count = Users.objects.filter(
                last_active__date=date
            ).count()
            
            # Use the higher of the two or combine them
            traffic_data.append(max(count, recent_count))
        
        return JsonResponse({
            'labels': dates,
            'data': traffic_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_user_demographics_api(request):
    """Get user demographics (admins, staff, officers)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Admin demographics
        admins = Admin.objects.all()
        admin_demo = {
            'total': admins.count(),
            'male': admins.filter(gender='male').count(),
            'female': admins.filter(gender='female').count(),
            'others': admins.filter(gender='others').count(),
            'verified': admins.filter(user__verification_status='verified').count(),
            'pending': admins.filter(user__verification_status='pending').count()
        }
        
        # Staff demographics
        staff = AccountStaff.objects.all()
        staff_demo = {
            'total': staff.count(),
            'male': staff.filter(gender='male').count(),
            'female': staff.filter(gender='female').count(),
            'others': staff.filter(gender='others').count(),
            'verified': staff.filter(user__verification_status='verified').count(),
            'pending': staff.filter(user__verification_status='pending').count()
        }
        
        # Officers demographics
        officers = Officers.objects.all()
        officer_demo = {
            'total': officers.count(),
            'male': officers.filter(gender='male').count(),
            'female': officers.filter(gender='female').count(),
            'others': officers.filter(gender='others').count(),
            'verified': officers.filter(user__verification_status='verified').count() if officers.exists() else 0,
            'pending': officers.filter(user__verification_status='pending').count() if officers.exists() else 0
        }
        
        return JsonResponse({
            'admins': admin_demo,
            'staff': staff_demo,
            'officers': officer_demo
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_admins_list_api(request):
    """Get list of all admins (admin only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        admins = Admin.objects.select_related('user').all()
        
        admins_list = []
        for admin in admins:
            gender_display = admin.gender.title() if admin.gender else 'N/A'
            admins_list.append({
                'name': admin.fullname or admin.user.username if admin.user else 'N/A',
                'position': admin.position or 'N/A',
                'gender': gender_display,
                'email': admin.email or 'N/A'
            })
        
        return JsonResponse({'admins': admins_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_staff_list_api(request):
    """Get list of all staff (admin only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        staff_list = AccountStaff.objects.select_related('user').all()
        
        staff_data = []
        for staff in staff_list:
            gender_display = staff.gender.title() if staff.gender else 'N/A'
            staff_data.append({
                'name': staff.fullname or staff.user.username if staff.user else 'N/A',
                'position': staff.position or 'N/A',
                'gender': gender_display,
                'email': staff.email or 'N/A'
            })
        
        return JsonResponse({'staff': staff_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_officers_list_api(request):
    """Get list of all officers (admin only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        officers = Officers.objects.select_related('coop', 'user').all()[:100]  # Limit to 100
        
        officers_list = []
        for officer in officers:
            gender_display = officer.gender.title() if officer.gender else 'N/A'
            officers_list.append({
                'name': officer.fullname or (officer.user.username if officer.user else 'N/A'),
                'position': officer.position or 'N/A',
                'cooperative': officer.coop.cooperative_name if officer.coop else 'N/A',
                'gender': gender_display
            })
        
        return JsonResponse({'officers': officers_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_cooperative_demographics_api(request):
    """Get comprehensive cooperative demographics with filters"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        # Get filter parameters
        category_filter = request.GET.get('category', '')
        district_filter = request.GET.get('district', '')
        
        # Apply filters
        filtered_coops = user_coops
        if category_filter:
            filtered_coops = filtered_coops.filter(category=category_filter)
        if district_filter:
            filtered_coops = filtered_coops.filter(district=district_filter)
        
        filtered_coop_ids = list(filtered_coops.values_list('coop_id', flat=True))
        
        # Category distribution
        categories = {}
        category_data = filtered_coops.values('category').annotate(count=Count('coop_id'))
        for c in category_data:
            cat = c['category'] or 'Not Specified'
            categories[cat] = c['count']
        
        # District distribution
        districts = {}
        district_data = filtered_coops.values('district').annotate(count=Count('coop_id'))
        for d in district_data:
            dist = d['district'] or 'Not Specified'
            districts[dist] = d['count']
        
        # Business activity distribution
        business_activities = {}
        if filtered_coop_ids:
            profiles = ProfileData.objects.filter(
                coop__coop_id__in=filtered_coop_ids
            ).values('business_activity').annotate(count=Count('coop', distinct=True))
            for p in profiles:
                activity = p['business_activity'] or 'Not Specified'
                business_activities[activity] = p['count']
        
        # Member demographics for filtered cooperatives
        member_demo = {'male': 0, 'female': 0, 'others': 0, 'total': 0}
        if filtered_coop_ids:
            members = Member.objects.filter(coop__coop_id__in=filtered_coop_ids)
            for member in members:
                member_demo['total'] += 1
                gender = (member.gender or '').lower()
                if gender == 'male':
                    member_demo['male'] += 1
                elif gender == 'female':
                    member_demo['female'] += 1
                else:
                    member_demo['others'] += 1
        
        # Financial summary
        financial_summary = {'total_assets': 0, 'total_capital': 0, 'total_surplus': 0}
        if filtered_coop_ids:
            financial_data = FinancialData.objects.filter(coop__coop_id__in=filtered_coop_ids)
            for coop_id in filtered_coop_ids:
                latest = financial_data.filter(coop__coop_id=coop_id).order_by('-report_year').first()
                if latest:
                    financial_summary['total_assets'] += float(latest.assets)
                    financial_summary['total_capital'] += float(latest.paid_up_capital)
                    financial_summary['total_surplus'] += float(latest.net_surplus)
        
        # Compliance status
        compliance = {'coc_active': 0, 'coc_inactive': 0, 'cote_active': 0, 'cote_inactive': 0}
        if filtered_coop_ids:
            profiles = ProfileData.objects.filter(coop__coop_id__in=filtered_coop_ids)
            for profile in profiles:
                if profile.coc_renewal:
                    compliance['coc_active'] += 1
                else:
                    compliance['coc_inactive'] += 1
                if profile.cote_renewal:
                    compliance['cote_active'] += 1
                else:
                    compliance['cote_inactive'] += 1
        
        return JsonResponse({
            'categories': categories,
            'districts': districts,
            'business_activities': business_activities,
            'member_demographics': member_demo,
            'financial_summary': financial_summary,
            'compliance': compliance,
            'total_cooperatives': filtered_coops.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

