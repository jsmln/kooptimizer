from django.urls import path
from . import views

app_name = 'databank' 

urlpatterns = [
    path('databank/', views.databank_management_view, name='databank_management'),
]