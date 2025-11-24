from django.shortcuts import render

def download_view(request):
    # We don't have a download.html, so just render the home for now
    return render(request, 'download.html') 

def about_view(request):
    # Render the about page
    return render(request, 'about.html')

def access_denied_view(request):
    """
    Shows access denied page for unauthenticated users
    """
    return render(request, 'access_denied.html', status=403)