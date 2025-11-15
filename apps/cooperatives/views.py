from django.shortcuts import render
from django.http import HttpResponse

# ... (You might have other imports) ...

# ADD THIS FUNCTION
def profile_form_view(request):
    return render(request, 'cooperatives/profile_form.html')