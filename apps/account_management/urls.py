from django.urls import path
from . import views

app_name = 'account_management'

urlpatterns = [
    # This is the path for your main page
    path('account_management/', views.account_management, name='account_management'),
    
    # ADD THIS NEW LINE for the API
    path('api/send-credentials/', views.send_credentials_view, name='send_credentials'),
]