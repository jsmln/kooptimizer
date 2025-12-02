from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('contact-support/', views.contact_view, name='contact_support'),
    path('first-login-setup/', views.first_login_setup, name='first_login_setup'),
    # Add other user-related URLs as needed
    # Profile Settings Page
    path('settings/', views.profile_settings, name='profile_settings'),
    
    # Form Submission Handler
    path('settings/update/', views.update_profile, name='update_profile'),

    path('password-reset/init/', views.initiate_password_reset, name='initiate_password_reset'),
    path('password-reset/verify/', views.perform_password_reset, name='perform_password_reset'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    path('all_events/', views.all_events, name='all_events'),
    path('add_event/', views.add_event, name='add_event'),
    path('update_event/<int:event_id>/', views.update_event, name='update_event'),
]
