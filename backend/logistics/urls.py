#backend/logistics/urls.py
from django.urls import path
from . import views

app_name = "logistics"

urlpatterns = [
    path("delta/evaluate/", views.run_delta_view, name="evaluate_delta"),
    # path("upload/", views.upload_invoice_view, name="upload_invoice"),
    # path("dashboard/", views.dashboard_view, name="logistics_dashboard"),
]
