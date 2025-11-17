from django.urls import path
from . import views

app_name = 'communications' 

urlpatterns = [
    # Messages
    path('message/', views.message_view, name='message'),
    path('api/message/contacts/', views.get_message_contacts, name='get_message_contacts'),
    path('api/message/conversation/<int:receiver_id>/', views.get_conversation, name='get_conversation'),
    path('api/message/send/', views.send_message, name='send_message'),
    path('api/message/attachment/<int:message_id>/', views.download_attachment, name='download_attachment'),
    path('api/message/attachment/<int:message_id>/convert-pdf/', views.convert_attachment_to_pdf, name='convert_attachment_to_pdf'),
    
    # Announcements
    path('announcement/send', views.handle_announcement, name='handle_announcement'),
    path('announcement/', views.announcement_view, name='announcement_form'),
]