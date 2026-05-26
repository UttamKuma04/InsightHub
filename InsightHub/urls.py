"""Root URL configuration for the InsightHub API."""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core.serializers import LoginTokenObtainPairView, RegisterView
from apps.dashboard.views import DashboardDrilldownView, DashboardSummaryView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", LoginTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/register", RegisterView.as_view(), name="register"),
    path("api/auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/upload/", include("apps.ingestion.upload_urls")),
    path("api/", include("apps.ingestion.record_urls")),
    path("api/review/", include("apps.review.urls")),
    path("api/audit", include("apps.audit.urls")),
    path("api/dashboard", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("api/dashboard/drilldown", DashboardDrilldownView.as_view(), name="dashboard-drilldown"),
]
