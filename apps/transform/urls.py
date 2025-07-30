from django.urls import path
from . import views

urlpatterns = [
    path('transform_data/', views.transform_data, name='transform_data'),  # matches /transform/
]
