from django.urls import path
from . import views

app_name = 'communications' 

urlpatterns = [
    path('message/', views.your_message_view, name='message'),
    path('announcement/', views.your_announcement_view, name='announcement_form'),
]