from django.urls import path
from . import views

app_name = 'account_management'

urlpatterns = [
     path('account_management/', views.account_management, name='account_management'),
]
