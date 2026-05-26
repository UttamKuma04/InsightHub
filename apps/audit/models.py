from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        EDIT = "EDIT", "Edit"
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        DELETE = "DELETE", "Delete"

    action = models.CharField(max_length=20, choices=Action.choices)
    record_type = models.CharField(max_length=30)
    record_id = models.PositiveBigIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="audit_logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["record_type", "record_id"], name="audit_record_idx"),
            models.Index(fields=["action"], name="audit_action_idx"),
        ]

    def __str__(self):
        return f"{self.action} {self.record_type}#{self.record_id}"
