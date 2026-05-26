from rest_framework import serializers

from apps.validation_service.models import ValidationIssue


class ValidationIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationIssue
        fields = ("id", "record_type", "record_id", "severity", "message", "created_at")

