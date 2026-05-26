from django.urls import path

from apps.ingestion.views import (
    ElectricityRecordViewSet,
    FuelRecordViewSet,
    TravelRecordViewSet,
)

urlpatterns = [
    path("fuel", FuelRecordViewSet.as_view({"get": "list"}), name="fuel-records"),
    path(
        "fuel/<int:pk>",
        FuelRecordViewSet.as_view({"delete": "destroy", "patch": "partial_update"}),
        name="fuel-record-detail",
    ),
    path("electricity", ElectricityRecordViewSet.as_view({"get": "list"}), name="electricity-records"),
    path(
        "electricity/<int:pk>",
        ElectricityRecordViewSet.as_view({"delete": "destroy", "patch": "partial_update"}),
        name="electricity-record-detail",
    ),
    path("travel", TravelRecordViewSet.as_view({"get": "list"}), name="travel-records"),
    path(
        "travel/<int:pk>",
        TravelRecordViewSet.as_view({"delete": "destroy", "patch": "partial_update"}),
        name="travel-record-detail",
    ),
]
