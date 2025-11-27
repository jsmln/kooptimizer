from django.urls import path
from . import views

app_name = 'cooperatives' 

urlpatterns = [
    # Main page to view form
    path('profile_form/', views.profile_form_view, name='profile_form'),
    
    # Action to save the form (AJAX POST)
    path('profiles/create/', views.create_profile, name='create_profile'),
    
    # Action to download files
    path('profiles/<int:coop_id>/attachment/<str:which>/', views.download_attachment, name='download_attachment'),
]