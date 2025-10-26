from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('cooperative/', views.cooperative_dashboard, name='cooperative_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
]