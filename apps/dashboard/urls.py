# apps/dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Home (GET for filters & metrics, POST for file upload)
    path('dashboard/', views.dashboard_home, name='dashboard_home'),

    # Optional: Separate upload endpoint (not mandatory if you're handling it via POST on same URL)
    # path('dashboard/upload/', views.upload_csv, name='upload_csv'),
]
