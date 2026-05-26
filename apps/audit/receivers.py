from django.dispatch import receiver

from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log
from apps.ingestion.signals import record_created


@receiver(record_created, dispatch_uid="audit_service_record_created")
def audit_record_created(sender, record, user=None, **kwargs):
    create_audit_log(
        AuditLog.Action.CREATE,
        record,
        user,
        details={"source_file": record.datasource.filename},
    )

