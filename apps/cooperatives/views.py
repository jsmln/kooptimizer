from django.shortcuts import render
from django.http import HttpResponse

def profile_form_view(request):
    """Display the cooperative profile form (existing view)"""
    return render(request, 'cooperatives/profile_form.html')

def profile_history_view(request):
    """Display the profile history table with modal form"""
    return render(request, 'cooperatives/profile_history.html')

# Alias for the default profile view (shows history table instead of form)
def profile_view(request):
    """Default profile view - shows history table"""
    return profile_history_view(request)