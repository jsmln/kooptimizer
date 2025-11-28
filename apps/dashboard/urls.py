from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('cooperative/', views.cooperative_dashboard, name='cooperative_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    
    # API endpoints
    path('api/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/charts/', views.dashboard_charts_api, name='dashboard_charts_api'),
    path('api/cooperatives/', views.dashboard_cooperatives_list_api, name='dashboard_cooperatives_list_api'),
    path('api/staff-workload/', views.dashboard_staff_workload_api, name='dashboard_staff_workload_api'),
    path('api/pending-reviews/', views.dashboard_pending_reviews_api, name='dashboard_pending_reviews_api'),
    path('api/recent-activity/', views.dashboard_recent_activity_api, name='dashboard_recent_activity_api'),
    path('api/member-demographics/', views.dashboard_member_demographics_api, name='dashboard_member_demographics_api'),
    path('api/user-traffic/', views.dashboard_user_traffic_api, name='dashboard_user_traffic_api'),
    path('api/user-demographics/', views.dashboard_user_demographics_api, name='dashboard_user_demographics_api'),
    path('api/admins-list/', views.dashboard_admins_list_api, name='dashboard_admins_list_api'),
    path('api/staff-list/', views.dashboard_staff_list_api, name='dashboard_staff_list_api'),
    path('api/officers-list/', views.dashboard_officers_list_api, name='dashboard_officers_list_api'),
    path('api/cooperative-demographics/', views.dashboard_cooperative_demographics_api, name='dashboard_cooperative_demographics_api'),
]