from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log
from apps.ingestion.models import ElectricityRecord, FuelRecord, RecordStatus, TravelRecord


RECORD_MODELS = {
    FuelRecord.RECORD_TYPE: FuelRecord,
    ElectricityRecord.RECORD_TYPE: ElectricityRecord,
    TravelRecord.RECORD_TYPE: TravelRecord,
}


@transaction.atomic
def approve_record(record_type, record_id, user):
    record = _get_reviewable_record(record_type, record_id, user)
    record.status = RecordStatus.APPROVED
    record.locked = True
    record.save(update_fields=["status", "locked"])
    create_audit_log(AuditLog.Action.APPROVE, record, user)
    return record


@transaction.atomic
def reject_record(record_type, record_id, user):
    record = _get_reviewable_record(record_type, record_id, user)
    record.status = RecordStatus.REJECTED
    record.locked = False
    record.save(update_fields=["status", "locked"])
    create_audit_log(AuditLog.Action.REJECT, record, user)
    return record


def _get_reviewable_record(record_type, record_id, user):
    model = RECORD_MODELS.get(record_type)
    if not model:
        raise ValidationError("Unsupported record type.")

    try:
        record = model.objects.select_for_update().select_related("datasource").get(id=record_id)
    except model.DoesNotExist as exc:
        raise NotFound("Record not found.") from exc

    if record.datasource.tenant_id != user.tenant_id:
        raise PermissionDenied("Cannot review records from another tenant.")
    if record.locked:
        raise ValidationError("Approved records are locked and cannot be changed.")
    return record

