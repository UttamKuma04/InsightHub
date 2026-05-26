from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "record_type", "record_id", "user", "timestamp")
    list_filter = ("action", "record_type")
    search_fields = ("record_type", "record_id", "user__email")

