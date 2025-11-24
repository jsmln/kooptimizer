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
    path('announcement/', views.announcement_view, name='announcement_form'),
    path('announcement/send/', views.handle_announcement, name='handle_announcement'),  # Added trailing slash
    path('api/announcement/draft/<int:announcement_id>/', views.get_draft_announcement, name='get_draft_announcement'),
    path('api/announcement/<int:announcement_id>/', views.get_announcement_details, name='get_announcement_details'),
    path('api/announcement/<int:announcement_id>/attachment/', views.download_announcement_attachment, name='download_announcement_attachment'),
    path('api/announcement/<int:announcement_id>/attachment/convert-pdf/', views.convert_announcement_attachment_to_pdf, name='convert_announcement_to_pdf'),
    path('api/announcement/cancel-schedule/<int:announcement_id>/', views.cancel_scheduled_announcement, name='cancel_scheduled_announcement'),
    path('api/announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),

    path('api/activity/recent/', views.get_recent_activity, name='api_recent_activity'),
]