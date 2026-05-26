from apps.audit.models import AuditLog


def create_audit_log(action, record, user, details=None):
    return AuditLog.objects.create(
        action=action,
        record_type=record.RECORD_TYPE,
        record_id=record.id,
        user=user if getattr(user, "is_authenticated", False) else None,
        details=details or {},
    )


def create_audit_logs(action, records, user, details_factory=None):
    actor = user if getattr(user, "is_authenticated", False) else None
    logs = [
        AuditLog(
            action=action,
            record_type=record.RECORD_TYPE,
            record_id=record.id,
            user=actor,
            details=details_factory(record) if details_factory else {},
        )
        for record in records
    ]
    return AuditLog.objects.bulk_create(logs) if logs else []
