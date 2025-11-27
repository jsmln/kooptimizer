from django.urls import path
from . import views

app_name = 'databank' 

urlpatterns = [
    path('databank/', views.databank_management_view, name='databank_management'),
    path('api/ocr/process/', views.process_ocr, name='process_ocr'),
    
    # Cooperative CRUD endpoints
    path('api/cooperative/add/', views.add_cooperative, name='add_cooperative'),
    path('api/cooperative/<int:coop_id>/', views.get_cooperative, name='get_cooperative'),
    path('api/cooperative/<int:coop_id>/update/', views.update_cooperative, name='update_cooperative'),
    path('api/cooperative/<int:coop_id>/delete/', views.delete_cooperative, name='delete_cooperative'),
    path('api/cooperative/<int:coop_id>/restore/', views.restore_cooperative, name='restore_cooperative'),
]