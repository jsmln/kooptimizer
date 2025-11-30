from django.urls import path
from . import views

app_name = 'databank' 

urlpatterns = [
    path('databank/', views.databank_management_view, name='databank_management'),
    path('api/ocr/process/', views.process_ocr, name='process_ocr'),
    path('api/ocr/sessions/', views.get_ocr_sessions, name='get_ocr_sessions'),
    path('api/ocr/sessions/<int:session_id>/consume/', views.mark_ocr_session_consumed, name='mark_ocr_session_consumed'),
    
    # Cooperative CRUD endpoints
    path('api/cooperative/add/', views.add_cooperative, name='add_cooperative'),
    path('api/cooperative/<int:coop_id>/', views.get_cooperative, name='get_cooperative'),
    path('api/cooperative/<int:coop_id>/update/', views.update_cooperative, name='update_cooperative'),
    path('api/cooperative/<int:coop_id>/delete/', views.delete_cooperative, name='delete_cooperative'),
    path('api/cooperative/<int:coop_id>/restore/', views.restore_cooperative, name='restore_cooperative'),
    path('api/verify-password/', views.verify_password_view, name='verify_password'),
    
    # Profile data endpoint
    path('api/profile-data/', views.get_profile_data, name='get_profile_data'),
    path('api/get-profile-details/<int:profile_id>/', views.get_profile_details, name='get_profile_details'),
    path('api/get-profile-for-edit/<int:profile_id>/', views.get_profile_for_edit, name='get_profile_for_edit'),
    path('api/update-profile/<int:profile_id>/', views.update_profile_from_databank, name='update_profile_from_databank'),
    path('api/approve-profile/<int:profile_id>/', views.approve_profile, name='approve_profile'),
]