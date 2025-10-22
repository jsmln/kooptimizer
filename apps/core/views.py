from django.shortcuts import render

def download_view(request):
    # We don't have a download.html, so just render the home for now
    return render(request, 'home.html') 

def about_view(request):
    # We don't have an about.html, so just render the home for now
    return render(request, 'home.html')