import logging
from time import monotonic

from celery import shared_task
from django.utils import timezone

from apps.core.cache import bump_tenant_cache_version
from apps.ingestion import services
from apps.ingestion.models import DataSource, UploadJob


logger = logging.getLogger(__name__)


INGESTION_HANDLERS = {
    DataSource.SourceType.SAP: services.ingest_sap_fuel_csv,
    DataSource.SourceType.UTILITY: services.ingest_utility_csv,
    DataSource.SourceType.TRAVEL: services.ingest_travel_csv,
}


@shared_task
def process_upload_job(upload_job_id):
    started = monotonic()
    job = UploadJob.objects.select_related("uploaded_by", "tenant").get(id=upload_job_id)
    logger.info("Starting upload job %s (%s, %s).", job.id, job.source_type, job.original_filename)
    job.status = UploadJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.finished_at = None
    job.total_records = 0
    job.error_message = ""
    job.save(update_fields=["status", "started_at", "finished_at", "total_records", "error_message"])

    try:
        handler = INGESTION_HANDLERS[job.source_type]
        with job.file.open("rb") as uploaded_file:
            uploaded_file.name = job.original_filename
            datasource, records = handler(uploaded_file, job.uploaded_by)

        job.status = UploadJob.Status.COMPLETED
        job.total_records = len(records)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "total_records", "finished_at"])
        bump_tenant_cache_version(job.tenant_id)
        logger.info(
            "Completed upload job %s with %s records in %.2f seconds.",
            job.id,
            len(records),
            monotonic() - started,
        )
        return {"datasource_id": datasource.id, "created_records": len(records)}
    except Exception as exc:
        job.status = UploadJob.Status.FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        logger.exception("Upload job %s failed after %.2f seconds.", job.id, monotonic() - started)
        raise
