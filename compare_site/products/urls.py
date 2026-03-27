# products/urls.py
from django.urls import path
from .views import home, upload_image_api

urlpatterns = [
    path('', home, name='home'),
    path('api/upload/', upload_image_api, name='upload_api'),
]