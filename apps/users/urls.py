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

    path('password-reset/init/', views.initiate_password_reset, name='initiate_password_reset'),
    path('password-reset/verify/', views.perform_password_reset, name='perform_password_reset'),

    path('all_events/', views.all_events, name='all_events'),
    path('add_event/', views.add_event, name='add_event'),
]
