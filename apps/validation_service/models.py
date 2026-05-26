from django.db import models


class ValidationIssue(models.Model):
    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    record_type = models.CharField(max_length=30)
    record_id = models.PositiveBigIntegerField()
    severity = models.CharField(max_length=20, choices=Severity.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "validation_issues"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["record_type", "record_id"], name="validation_record_idx"),
            models.Index(fields=["severity"], name="validation_severity_idx"),
        ]

    def __str__(self):
        return f"{self.severity} {self.record_type}#{self.record_id}: {self.message}"
