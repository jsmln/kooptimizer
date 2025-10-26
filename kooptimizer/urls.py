from django.contrib import admin
from django.urls import path
from apps.users import views as user_views  # This imports new view
from apps.home import views as home_views
from apps.core import views as core_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # This is new homepage URL:
    # It says when a user visits the root path (''),
    # run the 'login_view' function from user_views file.
    path('', user_views.login_view, name='login'), 
    path('home/', home_views.home_view, name='home'),
    path('download/', core_views.download_view, name='download'),
    path('about/', core_views.about_view, name='about'),


]

# serves as static files (CSS/JS) during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)