from django.contrib import admin

from apps.validation_service.models import ValidationIssue


@admin.register(ValidationIssue)
class ValidationIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "record_type", "record_id", "severity", "message", "created_at")
    list_filter = ("severity", "record_type")
    search_fields = ("message",)

