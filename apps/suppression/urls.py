from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('suppression_master/', views.suppression_master, name='suppression_master'),
    path('download-suppression/', views.download_suppression_csv, name='download_suppression_csv'),
    path('suppression_option/', views.suppression_option, name='suppression_option'),
    path('upload/', views.upload_file, name='upload_file'),
    path('map/', views.map_columns, name='map_columns'),
    path('download_mapped_file/', views.download_mapped_file, name='download_mapped_file'),
    path('upload_dump/', views.upload_dump, name='upload_dump'),
    path('map_columns_dump/', views.map_columns_dump, name='map_columns_dump'),

        # Add other paths as needed
]




# Serve media files in development (make sure this is added at the bottom of the URL patterns)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
