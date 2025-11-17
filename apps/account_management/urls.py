from django.urls import path
from . import views

app_name = 'account_management'

urlpatterns = [
    path('account_management/', views.account_management, name='account_management'),
    
    path('api/send-credentials/', views.send_credentials_view, name='send_credentials'),
    path('api/get-user-details/<int:user_id>/', views.get_user_details_view, name='get_user_details'),
    path('api/update-user/<int:user_id>/', views.update_user_view, name='update_user'),
    path('api/deactivate-user/<int:user_id>/', views.deactivate_user_view, name='deactivate_user'),
]