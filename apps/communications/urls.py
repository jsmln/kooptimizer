from django.urls import path
from . import views

app_name = 'communications' 

urlpatterns = [
    path('message/', views.message_view, name='message'),
    path('announcement/send', views.handle_announcement, name='handle_announcement'),
    path('announcement/', views.announcement_view, name='announcement_form'),
]