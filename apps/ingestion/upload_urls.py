from django.urls import path

from apps.ingestion.views import (
    SapUploadView,
    TravelUploadView,
    UploadJobListView,
    UploadJobRetryView,
    UploadJobStatusView,
    UtilityUploadView,
)

urlpatterns = [
    path("sap", SapUploadView.as_view(), name="upload-sap"),
    path("utility", UtilityUploadView.as_view(), name="upload-utility"),
    path("travel", TravelUploadView.as_view(), name="upload-travel"),
    path("jobs", UploadJobListView.as_view(), name="upload-job-list"),
    path("jobs/<int:pk>", UploadJobStatusView.as_view(), name="upload-job-status"),
    path("jobs/<int:pk>/retry", UploadJobRetryView.as_view(), name="upload-job-retry"),
]
