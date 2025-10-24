from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('first-login-setup/', views.first_login_setup, name='first_login_setup'),
    # Add other user-related URLs as needed
]
