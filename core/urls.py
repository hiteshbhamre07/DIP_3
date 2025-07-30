from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Add this import
from django.conf.urls.static import static  # Add this import

urlpatterns = [
    path('admin/',admin.site.urls),  # Django admin route
    path('', include('apps.authentication.urls')),  # Authentication app
    path('', include('apps.home.urls')),  # Home app
    path('', include('apps.suppression.urls')),  # Suppression app path
    path('', include('apps.reports.urls')),  # Reports app path
    path('',include('apps.transform.urls')),  # Transform app path
    path('',include('apps.dashboard.urls')),  # Dashboard app path
]

# Serve media files during development #python -m pip install django
# python -m pip install -r requirements.txt
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




