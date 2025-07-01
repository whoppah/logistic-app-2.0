#backend/logistics/urls.py
from django.urls import path
from .views import CheckDeltaView 

app_name = "logistics"

urlpatterns = [
    path("check-delta/", CheckDeltaView.as_view(), name="check-delta"),
]
