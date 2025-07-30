from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Regular pages for the report section
    path('reports_option/', views.reports_option, name='reports_option'),
    path('upload_reports/', views.upload_form, name='upload_form'),
    path('submit_report/', views.submit_report, name='submit_report'),
    path('generate_reports/', views.generate_reports, name='generate_reports'),
    path('download_pdf/<str:filename>/', views.download_report_as_pdf, name='download_report_as_pdf'),

    # # API Endpoints for external interaction with PHP CRM
    # path('api/get-campaign-data/', views.get_campaign_data_from_php_crm, name='get_campaign_data_from_php_crm'),
    # # API to get data from PHP CRM
    # path('api/send-report/', views.submit_report_to_crm, name='submit_report_to_crm'),  # API to send report to PHP CRM
    # path('api/', views.api_home, name='api_home'),
    # Add the receive_data endpoint
    # path('fetch-php-data/', views.fetch_from_php, name='fetch_php_data'),
    path('api/receive_data/',views.receive_data, name='receive_data'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
