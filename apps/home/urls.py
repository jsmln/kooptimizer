from django.urls import path
from . import views

urlpatterns = [
    # Map the URL path 'home/' to the home_view function
    # The name='home' is what you used in the redirect('home') call
    path('home/', views.home_view, name='home'), 
]