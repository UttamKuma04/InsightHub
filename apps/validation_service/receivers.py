from django.dispatch import receiver

from apps.ingestion.signals import record_created
from apps.validation_service.services import validate_record


@receiver(record_created, dispatch_uid="validation_service_record_created")
def run_validation_on_record_created(sender, record, **kwargs):
    validate_record(record)

