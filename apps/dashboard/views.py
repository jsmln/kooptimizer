from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from .analytics import get_analytics_data

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

@login_required
@role_required(['admin'])
def admin_dashboard(request):
    
    # 1. Fetch Analytics Data (Runs in background)
    analytics_data = get_analytics_data()

    # 2. Prepare Context
    context = {
        'page_title': 'Admin Dashboard',
        
        # Pass the data to the template
        'chart_labels': analytics_data['labels'],
        'chart_data': analytics_data['data'],
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@role_required(['officer'])
def cooperative_dashboard(request):
    return render(request, 'dashboard/cooperative_dashboard.html', {
        'page_title': 'Cooperative Dashboard'
    })


@login_required
@role_required(['staff'])
def staff_dashboard(request):
    return render(request, 'dashboard/staff_dashboard.html', {
        'page_title': 'Staff Dashboard'
    })

