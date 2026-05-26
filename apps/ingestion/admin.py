from django.contrib import admin

from apps.ingestion.models import DataSource, ElectricityRecord, FuelRecord, TravelRecord, UploadJob


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "source_type", "filename", "uploaded_by", "uploaded_at")
    list_filter = ("source_type", "tenant")
    search_fields = ("filename",)


@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "source_type", "original_filename", "status", "total_records", "created_at")
    list_filter = ("source_type", "status", "tenant")
    search_fields = ("original_filename",)
    readonly_fields = ("created_at", "started_at", "finished_at")


@admin.register(FuelRecord)
class FuelRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "datasource", "date", "fuel_type", "quantity", "unit", "status", "locked")
    list_filter = ("status", "locked", "fuel_type")


@admin.register(ElectricityRecord)
class ElectricityRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "datasource", "meter_id", "billing_start", "billing_end", "kwh", "status", "locked")
    list_filter = ("status", "locked")


@admin.register(TravelRecord)
class TravelRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "datasource", "trip_type", "origin", "destination", "distance_km", "status", "locked")
    list_filter = ("status", "locked", "trip_type")
