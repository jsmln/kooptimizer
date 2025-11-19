from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('first-login-setup/', views.first_login_setup, name='first_login_setup'),
    # Add other user-related URLs as needed
    # Profile Settings Page
    path('settings/', views.profile_settings, name='profile_settings'),
    
    # Form Submission Handler
    path('settings/update/', views.update_profile, name='update_profile'),
]
