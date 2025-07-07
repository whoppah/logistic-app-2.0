#backend/logistics/urls.py
from django.urls import path
from .views import CheckDeltaView, UploadInvoiceFile, TaskStatusView, TaskResultView, AnalyticsView

app_name = "logistics"

urlpatterns = [
    path("upload/", UploadInvoiceFile.as_view(), name="upload-invoice"),
    path("check-delta/", CheckDeltaView.as_view(), name="check-delta"),
    path("task-status/", TaskStatusView.as_view(), name="task-status"),
    path("task-result/", TaskResultView.as_view(), name="task-result"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
]
