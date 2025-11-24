from django.shortcuts import render, redirect

def home_view(request):
    # If user is already logged in, redirect to their dashboard
    if request.session.get('user_id'):
        role = request.session.get('role')
        if role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif role == 'officer':
            return redirect('dashboard:cooperative_dashboard')
        elif role == 'staff':
            return redirect('dashboard:staff_dashboard')
    
    # If not logged in, show the home page
    return render(request, 'home.html', {})