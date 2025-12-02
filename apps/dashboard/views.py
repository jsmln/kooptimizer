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
from django.contrib.auth.models import User as DjangoUser
from webpush.models import PushInformation

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
            # Import Officer from the correct place
            from apps.cooperatives.models import Officer as CoopOfficer
            officer = CoopOfficer.objects.filter(user_id=user_id).first()
            if officer:
                return Cooperatives.objects.filter(coop_id=officer.coop_id)
            return Cooperatives.objects.none()
        except:
            return Cooperatives.objects.none()
    return Cooperatives.objects.none()

def extract_district_from_address(address):
    """Extract district from address by matching barangay names"""
    if not address:
        return None
    
    address_lower = address.lower()
    
    # District mapping (barangays to districts) - using actual names from GeoJSON
    district_mapping = {
        "North": ["balintawak", "marauoy", "dagatan", "lumbang", "talisay", "bulacnin", "pusil", "bugtong na pulo", "inosloban", "plaridel", "san lucas"],
        "East": ["san francisco", "san celestino", "malitlit", "santo toribio", "san benito", "santo niño", "munting pulo", "latag", "sabang", "tipacan", "san jose", "tangob", "antipolo del norte", "antipolo del sur", "pinagkawitan"],
        "West": ["halang", "duhatan", "pinagtongulan", "bulaklakan", "pangao", "bagong pook", "abanaybanay", "tambo", "sico", "san salvador", "tanguay", "tibig", "san carlos", "mataas na lupa", "sapac"],
        "South": ["adya", "lodlod", "cumba", "quezon", "sampaguita", "san sebastian", "kayumanggi", "anilao", "anilao-labac", "pagolingin bata", "pagolingin east", "pagolingin west", "malagonlong", "bolbok", "rizal", "mabini", "calamias", "san guillermo"],
        "Urban": ["poblacion barangay 1", "poblacion barangay 2", "poblacion barangay 3", "poblacion barangay 4", "poblacion barangay 5", "poblacion barangay 6", "poblacion barangay 7", "poblacion barangay 8", "poblacion barangay 9", "poblacion barangay 9-a", "poblacion barangay 10", "poblacion barangay 11", "barangay 12", "poblacion"]
    }
    
    # Check each district's barangays
    for district, barangays in district_mapping.items():
        for barangay in barangays:
            # Check if barangay name appears in address
            if barangay in address_lower:
                return district
    
    return None

def get_districts_from_addresses(coop_ids):
    """Get district counts from ProfileData addresses"""
    districts = {}
    
    if not coop_ids:
        return districts
    
    # Get latest profile for each cooperative
    profiles = ProfileData.objects.filter(coop__coop_id__in=coop_ids).order_by('coop__coop_id', '-report_year')
    
    # Track which cooperatives we've already counted (use latest profile per coop)
    counted_coops = set()
    
    for profile in profiles:
        coop_id = profile.coop.coop_id
        if coop_id in counted_coops:
            continue
        
        counted_coops.add(coop_id)
        district = extract_district_from_address(profile.address)
        
        if district:
            districts[district] = districts.get(district, 0) + 1
    
    return districts

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
    profile_data = None
    
    try:
        officer = Officers.objects.filter(user_id=user_id).first()
        if officer:
            cooperative = officer.coop
            
            # Get latest ProfileData for this cooperative
            if cooperative:
                profile_data = ProfileData.objects.filter(
                    coop=cooperative
                ).order_by('-report_year', '-created_at').first()
    except Exception as e:
        print(f"Error in cooperative_dashboard: {e}")
        import traceback
        traceback.print_exc()
    
    # Create a simple object that combines cooperative and profile data for template
    class CooperativeContext:
        def __init__(self, coop, profile=None):
            # Cooperative fields
            self.coop_id = coop.coop_id if coop else None
            self.cooperative_name = coop.cooperative_name if coop else "Unknown Cooperative"
            
            # Profile data fields (use profile if available, otherwise None)
            if profile:
                self.address = profile.address
                self.cda_registration_number = profile.cda_registration_number
                self.cda_registration_date = profile.cda_registration_date
                self.lccdc_membership_date = profile.lccdc_membership_date
                self.lccdc_membership = profile.lccdc_membership
                self.business_activity = profile.business_activity
                self.operation_area = profile.operation_area
                self.board_of_directors_count = profile.board_of_directors_count
                self.salaried_employees_count = profile.salaried_employees_count
                self.coc_renewal = profile.coc_renewal
                self.cote_renewal = profile.cote_renewal
            else:
                self.address = None
                self.cda_registration_number = None
                self.cda_registration_date = None
                self.lccdc_membership_date = None
                self.lccdc_membership = None
                self.business_activity = None
                self.operation_area = None
                self.board_of_directors_count = None
                self.salaried_employees_count = None
                self.coc_renewal = None
                self.cote_renewal = None
    
    cooperative_context = CooperativeContext(cooperative, profile_data) if cooperative else None
    
    # Check if profile data exists (any profile data, not just latest)
    has_profile_data = False
    if cooperative:
        has_profile_data = ProfileData.objects.filter(coop=cooperative).exists()
    
    return render(request, 'dashboard/cooperative_dashboard.html', {
        'page_title': 'Cooperative Dashboard',
        'cooperative': cooperative_context,
        'profile_data': profile_data,
        'has_profile_data': has_profile_data
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
        
        # District Distribution - based on address from ProfileData
        districts = get_districts_from_addresses(coop_ids)
        
        # Compliance Status
        # Count certificates separately for chart display
        compliance_data = {'coc': {'active': 0, 'inactive': 0}, 'cote': {'active': 0, 'inactive': 0}, 'both_active': 0, 'total_profiles': 0}
        if coop_ids:
            profiles = ProfileData.objects.filter(coop__coop_id__in=coop_ids)
            compliance_data['total_profiles'] = profiles.count()
            for profile in profiles:
                coc_active = bool(profile.coc_renewal)
                cote_active = bool(profile.cote_renewal)
                
                if coc_active:
                    compliance_data['coc']['active'] += 1
                else:
                    compliance_data['coc']['inactive'] += 1
                    
                if cote_active:
                    compliance_data['cote']['active'] += 1
                else:
                    compliance_data['cote']['inactive'] += 1
                
                # Count cooperatives with BOTH certificates active
                if coc_active and cote_active:
                    compliance_data['both_active'] += 1
        
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
    """Get pending reviews (admin/staff only) - excludes approved items"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        pending_reviews = []
        if coop_ids:
            # Get all financial data for these cooperatives
            all_financial = FinancialData.objects.filter(
                coop__coop_id__in=coop_ids
            ).order_by('-created_at')[:20]
            
            for fin in all_financial:
                # Check if both profile and financial data are approved - if so, skip
                profile = ProfileData.objects.filter(
                    coop__coop_id=fin.coop.coop_id,
                    report_year=fin.report_year
                ).first()
                
                # If profile exists and both are approved, skip this item
                if profile and profile.approval_status == 'approved' and fin.approval_status == 'approved':
                    continue
                
                # Only include if at least one is pending (not both approved)
                if fin.approval_status == 'pending' or (profile and profile.approval_status == 'pending'):
                    coop = user_coops.filter(coop_id=fin.coop.coop_id).first()
                    if coop:
                        # Get assets from financial data
                        assets = float(fin.assets) if fin.assets else 0
                        pending_reviews.append({
                            'coop_name': coop.cooperative_name,
                            'year': fin.report_year,
                            'assets': assets,
                            'type': 'Financial Report',
                            'coop_id': coop.coop_id,
                            'fin_status': fin.approval_status,
                            'profile_status': profile.approval_status if profile else 'none'
                        })
            
            # Also check for profiles without financial data that are pending
            all_profiles = ProfileData.objects.filter(
                coop__coop_id__in=coop_ids
            ).order_by('-created_at')[:20]
            
            for profile in all_profiles:
                # Check if both profile and financial data are approved - if so, skip
                fin_data = FinancialData.objects.filter(
                    coop__coop_id=profile.coop.coop_id,
                    report_year=profile.report_year
                ).first()
                
                # If financial data exists and both are approved, skip this item
                if fin_data and fin_data.approval_status == 'approved' and profile.approval_status == 'approved':
                    continue
                
                # Only include if at least one is pending (not both approved)
                if profile.approval_status == 'pending' or (fin_data and fin_data.approval_status == 'pending'):
                    # Check if already in list
                    existing = next((r for r in pending_reviews if r['coop_name'] == profile.coop.cooperative_name and r['year'] == profile.report_year), None)
                    if not existing:
                        coop = user_coops.filter(coop_id=profile.coop.coop_id).first()
                        if coop:
                            assets = float(fin_data.assets) if fin_data and fin_data.assets else 0
                            pending_reviews.append({
                                'coop_name': coop.cooperative_name,
                                'year': profile.report_year,
                                'assets': assets,
                                'type': 'Profile',
                                'coop_id': coop.coop_id,
                                'fin_status': fin_data.approval_status if fin_data else 'none',
                                'profile_status': profile.approval_status
                            })
        
        # Remove duplicates and sort by most recent first
        seen = set()
        unique_reviews = []
        for review in pending_reviews:
            key = (review['coop_name'], review['year'])
            if key not in seen:
                seen.add(key)
                unique_reviews.append(review)
        
        unique_reviews.sort(key=lambda x: x['year'], reverse=True)
        
        return JsonResponse({'pending_reviews': unique_reviews[:10]})  # Limit to 10 most recent
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_recent_activity_api(request):
    """Get recent activity timeline"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        print(f"DEBUG dashboard_recent_activity_api: user_id={user_id}, role={role}")
        
        if not user_id or not role:
            print("DEBUG: No user_id or role in session")
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        print(f"DEBUG: Found coop_ids: {coop_ids}")
        
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
        
        print(f"DEBUG: Returning {len(activities)} activities")
        
        return JsonResponse({'activities': activities})
    except Exception as e:
        print(f"DEBUG ERROR in dashboard_recent_activity_api: {e}")
        import traceback
        traceback.print_exc()
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
        category_filter = request.GET.get('category', '').strip()
        district_filter = request.GET.get('district', '').strip()
        
        # Start with all user cooperatives
        filtered_coops = user_coops
        
        # Apply category filter (case-insensitive)
        if category_filter:
            # Normalize category filter to match database values
            category_filter_lower = category_filter.lower()
            filtered_coops = filtered_coops.filter(
                Q(category__iexact=category_filter) | 
                Q(category__iexact=category_filter_lower) |
                Q(category__iexact=category_filter.capitalize())
            )
        
        # Get initial filtered coop IDs
        initial_coop_ids = list(filtered_coops.values_list('coop_id', flat=True))
        
        # Apply district filter based on addresses from ProfileData
        filtered_coop_ids = initial_coop_ids
        if district_filter:
            # Filter cooperatives by district extracted from addresses
            if initial_coop_ids:
                # Get latest profile for each cooperative to extract district
                latest_profiles = ProfileData.objects.filter(
                    coop__coop_id__in=initial_coop_ids
                ).order_by('coop__coop_id', '-report_year').distinct('coop__coop_id')
                
                district_matched_coop_ids = []
                district_filter_lower = district_filter.lower()
                
                for profile in latest_profiles:
                    address = profile.address or ''
                    extracted_district = extract_district_from_address(address)
                    extracted_district_lower = extracted_district.lower() if extracted_district else ''
                    
                    # Case-insensitive district matching
                    if (extracted_district_lower == district_filter_lower or
                        extracted_district == district_filter or
                        extracted_district == district_filter.capitalize()):
                        district_matched_coop_ids.append(profile.coop.coop_id)
                
                filtered_coop_ids = district_matched_coop_ids
            else:
                filtered_coop_ids = []
        
        # Get final filtered cooperatives
        final_filtered_coops = user_coops.filter(coop_id__in=filtered_coop_ids) if filtered_coop_ids else user_coops.none()
        
        # Category distribution
        categories = {}
        if filtered_coop_ids:
            category_data = final_filtered_coops.values('category').annotate(count=Count('coop_id'))
            for c in category_data:
                cat = c['category'] or 'Not Specified'
                categories[cat] = c['count']
        
        # District distribution - based on address from ProfileData
        districts = get_districts_from_addresses(filtered_coop_ids) if filtered_coop_ids else {}
        
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
            'total_cooperatives': len(filtered_coop_ids) if filtered_coop_ids else 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_officer_data_api(request):
    """Get comprehensive data for officer dashboard (their cooperative only)"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or role != 'officer':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Get officer's cooperative
        officer = Officers.objects.filter(user_id=user_id).first()
        if not officer or not officer.coop_id:
            return JsonResponse({'error': 'No cooperative found'}, status=404)
        
        coop_id = officer.coop_id
        
        # Document Status (from latest ProfileData)
        latest_profile = ProfileData.objects.filter(coop__coop_id=coop_id).order_by('-report_year', '-created_at').first()
        document_status = {
            'coc': {
                'active': bool(latest_profile.coc_renewal) if latest_profile else False,
                'needs_renewal': not bool(latest_profile.coc_renewal) if latest_profile else True
            },
            'cote': {
                'active': bool(latest_profile.cote_renewal) if latest_profile else False,
                'needs_renewal': not bool(latest_profile.cote_renewal) if latest_profile else True
            },
            'lccdc': {
                'active': bool(latest_profile.lccdc_membership) if latest_profile else False
            }
        }
        
        # Officers List
        officers_list = []
        officers = Officers.objects.filter(coop_id=coop_id).select_related('user')
        for off in officers:
            officers_list.append({
                'name': off.fullname or (off.user.username if off.user else 'N/A'),
                'position': off.position or 'N/A',
                'gender': (off.gender or 'N/A').title()
            })
        
        # Financial Year-over-Year Growth (last 5 years)
        financial_growth = {'assets': {}, 'capital': {}, 'surplus': {}}
        current_year = datetime.now().year
        for year in range(current_year - 4, current_year + 1):
            year_data = FinancialData.objects.filter(
                coop__coop_id=coop_id,
                report_year=year
            ).first()
            
            if year_data:
                financial_growth['assets'][str(year)] = float(year_data.assets)
                financial_growth['capital'][str(year)] = float(year_data.paid_up_capital)
                financial_growth['surplus'][str(year)] = float(year_data.net_surplus)
            else:
                financial_growth['assets'][str(year)] = 0
                financial_growth['capital'][str(year)] = 0
                financial_growth['surplus'][str(year)] = 0
        
        # KPI Data from ProfileData
        kpi_data = {
            'total_employees': latest_profile.salaried_employees_count if latest_profile and latest_profile.salaried_employees_count else 0,
            'board_directors': latest_profile.board_of_directors_count if latest_profile and latest_profile.board_of_directors_count else 0,
            'profile_status': latest_profile.approval_status if latest_profile else 'pending',
            'report_year': latest_profile.report_year if latest_profile else None,
            'profile_created': latest_profile.created_at.strftime('%Y-%m-%d') if latest_profile and latest_profile.created_at else None,
            'profile_updated': latest_profile.updated_at.strftime('%Y-%m-%d') if latest_profile and latest_profile.updated_at else None,
        }
        
        # Latest Financial Data
        latest_financial = FinancialData.objects.filter(
            coop__coop_id=coop_id
        ).order_by('-report_year', '-created_at').first()
        
        financial_kpis = {
            'total_assets': float(latest_financial.assets) if latest_financial else 0,
            'paid_up_capital': float(latest_financial.paid_up_capital) if latest_financial else 0,
            'net_surplus': float(latest_financial.net_surplus) if latest_financial else 0,
            'financial_year': latest_financial.report_year if latest_financial else None,
        }
        
        # Count Members
        total_members = Member.objects.filter(coop__coop_id=coop_id).count()
        
        return JsonResponse({
            'document_status': document_status,
            'officers': officers_list,
            'financial_growth': financial_growth,
            'kpi_data': kpi_data,
            'financial_kpis': financial_kpis,
            'total_members': total_members,
            'total_officers': len(officers_list)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_cooperative_locations_api(request):
    """Get cooperative locations with district information for map markers"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        user_coops = get_user_cooperatives(user_id, role)
        coop_ids = list(user_coops.values_list('coop_id', flat=True))
        
        if not coop_ids:
            return JsonResponse({'cooperatives': [], 'districts': {}})
        
        # District center coordinates (approximate centers for Lipa City districts)
        district_centers = {
            "North": [13.98, 121.14],
            "East": [13.92, 121.20],
            "West": [13.92, 121.10],
            "South": [13.88, 121.15],
            "Urban": [13.9419, 121.1644]  # Lipa City center
        }
        
        # Get latest profile for each cooperative
        profiles = ProfileData.objects.filter(coop__coop_id__in=coop_ids).order_by('coop__coop_id', '-report_year')
        
        # Track which cooperatives we've already processed (use latest profile per coop)
        processed_coops = set()
        cooperatives = []
        district_counts = {}
        
        # Small random offset to spread markers in same district
        import random
        random.seed(42)  # For consistent positioning
        
        for profile in profiles:
            coop_id = profile.coop.coop_id
            if coop_id in processed_coops:
                continue
            
            processed_coops.add(coop_id)
            district = extract_district_from_address(profile.address)
            
            if district and district in district_centers:
                # Get base coordinates for district
                base_lat, base_lng = district_centers[district]
                
                # Add small random offset to spread markers (max 0.01 degrees ~1km)
                offset_lat = random.uniform(-0.008, 0.008)
                offset_lng = random.uniform(-0.008, 0.008)
                
                cooperatives.append({
                    'coop_id': coop_id,
                    'name': profile.coop.cooperative_name if profile.coop else 'Unknown',
                    'district': district,
                    'address': profile.address or '',
                    'latitude': base_lat + offset_lat,
                    'longitude': base_lng + offset_lng
                })
                
                # Count cooperatives per district
                district_counts[district] = district_counts.get(district, 0) + 1
        
        return JsonResponse({
            'cooperatives': cooperatives,
            'districts': district_counts
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_check_push_subscription_api(request):
    """Check if user has push notifications enabled"""
    try:
        user_id = request.session.get('user_id')
        role = request.session.get('role')
        
        if not user_id or not role:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Get custom user
        try:
            custom_user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'has_subscription': False})
        
        # Check if there's a Django User mapped to this custom user
        try:
            django_user = DjangoUser.objects.get(username=custom_user.username)
            # Check if user has any push subscriptions
            has_subscription = PushInformation.objects.filter(user=django_user).exists()
            return JsonResponse({'has_subscription': has_subscription})
        except DjangoUser.DoesNotExist:
            return JsonResponse({'has_subscription': False})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

