#backend/config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("logistics/", include("logistics.urls", namespace="logistics")),
    path("vite/", include("django_vite.urls")),
]
