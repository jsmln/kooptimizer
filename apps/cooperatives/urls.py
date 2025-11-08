from django.urls import path
from . import views

app_name = 'cooperatives' 

urlpatterns = [
    path('profile_form/', views.profile_form_view, name='profile_form'),
]