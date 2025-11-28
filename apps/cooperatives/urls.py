from django.urls import path
from . import views

app_name = 'cooperatives' 

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),  # Default - shows history table
    path('profile_form/', views.profile_form_view, name='profile_form'),  # Legacy form view
    path('profile_history/', views.profile_history_view, name='profile_history'),  # Explicit history view
]