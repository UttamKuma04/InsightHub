from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = ("id", "action", "record_type", "record_id", "user", "timestamp", "details")

