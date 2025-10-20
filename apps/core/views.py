from django.shortcuts import render

def download_view(request):
    # We don't have a download.html, so just render the dashboard for now
    return render(request, 'dashboard.html') 

def about_view(request):
    # We don't have an about.html, so just render the dashboard for now
    return render(request, 'dashboard.html')