import csv
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log
from apps.core.cache import bump_tenant_cache_version, get_cached, set_cached, tenant_cache_key
from apps.core.permissions import IsAnalystOrAdmin
from apps.ingestion import services
from apps.ingestion.models import ElectricityRecord, FuelRecord, RecordStatus, TravelRecord
from apps.ingestion.models import DataSource, UploadJob
from apps.ingestion.serializers import (
    ElectricityRecordSerializer,
    FuelRecordSerializer,
    TravelRecordSerializer,
    UploadSerializer,
)
from apps.ingestion.tasks import process_upload_job
from apps.validation_service.models import ValidationIssue
from apps.validation_service.serializers import ValidationIssueSerializer


logger = logging.getLogger(__name__)


class UploadServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Upload service is temporarily unavailable."
    default_code = "upload_service_unavailable"


LIST_FIELDS_BY_RECORD_TYPE = {
    FuelRecord.RECORD_TYPE: (
        "id",
        "ebeln",
        "ebelp",
        "bedat",
        "matnr",
        "txz01",
        "matkl",
        "werks",
        "quantity",
        "unit",
        "netwr",
        "bwart",
        "status",
        "locked",
    ),
    ElectricityRecord.RECORD_TYPE: (
        "id",
        "account_no",
        "meter_id",
        "site_name",
        "discom",
        "tariff_code",
        "billing_start",
        "billing_end",
        "billing_days",
        "read_type",
        "kwh",
        "consumption_unit",
        "total_bill_inr",
        "status",
        "locked",
    ),
    TravelRecord.RECORD_TYPE: (
        "id",
        "report_id",
        "expense_type",
        "transaction_date",
        "employee_id",
        "origin_iata",
        "destination_iata",
        "distance_km",
        "cabin_class",
        "hotel_city",
        "ground_transport_type",
        "amount",
        "approval_status",
        "status",
        "locked",
    ),
}

SEARCH_FIELDS_BY_RECORD_TYPE = {
    FuelRecord.RECORD_TYPE: ("ebeln", "ebelp", "matnr", "txz01", "matkl", "werks", "datasource__filename"),
    ElectricityRecord.RECORD_TYPE: ("account_no", "meter_id", "site_name", "discom", "tariff_code", "datasource__filename"),
    TravelRecord.RECORD_TYPE: (
        "report_id",
        "expense_type",
        "employee_id",
        "origin_iata",
        "destination_iata",
        "hotel_city",
        "datasource__filename",
    ),
}

DATE_FIELD_BY_RECORD_TYPE = {
    FuelRecord.RECORD_TYPE: "bedat",
    ElectricityRecord.RECORD_TYPE: "billing_start",
    TravelRecord.RECORD_TYPE: "transaction_date",
}


class BaseUploadView(APIView):
    permission_classes = [IsAnalystOrAdmin]
    source_type = None

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]

        try:
            upload_job = UploadJob.objects.create(
                tenant=request.user.tenant,
                uploaded_by=request.user,
                source_type=self.source_type,
                file=uploaded_file,
                original_filename=getattr(uploaded_file, "name", "upload.csv"),
            )
        except Exception as exc:
            logger.exception("Could not store uploaded CSV.")
            raise UploadServiceUnavailable(
                "Could not store uploaded CSV. Check S3 storage settings and bucket permissions."
            ) from exc

        try:
            process_upload_job.delay(upload_job.id)
        except Exception as exc:
            upload_job.status = UploadJob.Status.FAILED
            upload_job.error_message = "Could not queue upload job. Check Celery/Redis connection."
            upload_job.save(update_fields=["status", "error_message"])
            logger.exception("Could not queue upload job %s.", upload_job.id)
            raise UploadServiceUnavailable(upload_job.error_message) from exc

        return Response(
            {
                "upload_job_id": upload_job.id,
                "source_type": _choice_value(upload_job.source_type),
                "filename": upload_job.original_filename,
                "status": upload_job.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class SapUploadView(BaseUploadView):
    source_type = DataSource.SourceType.SAP


class UtilityUploadView(BaseUploadView):
    source_type = DataSource.SourceType.UTILITY


class TravelUploadView(BaseUploadView):
    source_type = DataSource.SourceType.TRAVEL


class UploadJobStatusView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request, pk):
        job = get_object_or_404(UploadJob, id=pk, tenant=request.user.tenant)
        return Response(
            {
                "upload_job_id": job.id,
                "source_type": job.source_type,
                "filename": job.original_filename,
                "status": job.status,
                "total_records": job.total_records,
                "error_message": job.error_message,
            }
        )


class UploadJobListView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        jobs = UploadJob.objects.filter(tenant=request.user.tenant).order_by("-created_at")[:20]
        return Response([_upload_job_data(job) for job in jobs])


class UploadJobRetryView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def post(self, request, pk):
        job = get_object_or_404(UploadJob, id=pk, tenant=request.user.tenant)
        if job.status != UploadJob.Status.FAILED:
            raise ValidationError("Only failed upload jobs can be retried.")
        try:
            file_exists = job.file.storage.exists(job.file.name)
        except Exception as exc:
            raise ValidationError("Cannot access the original uploaded file. Upload the CSV again.") from exc
        if not file_exists:
            raise ValidationError("Original uploaded file is not available. Upload the CSV again.")

        job.status = UploadJob.Status.QUEUED
        job.error_message = ""
        job.total_records = 0
        job.started_at = None
        job.finished_at = None
        job.save(update_fields=["status", "error_message", "total_records", "started_at", "finished_at"])
        transaction.on_commit(lambda: process_upload_job.delay(job.id))
        return Response(_upload_job_data(job), status=status.HTTP_202_ACCEPTED)


class TenantRecordViewSetMixin:
    permission_classes = [IsAnalystOrAdmin]

    def get_queryset(self):
        return (
            self.queryset.filter(datasource__tenant=self.request.user.tenant)
            .select_related("datasource", "datasource__uploaded_by")
        )

    def list(self, request, *args, **kwargs):
        record_type = self.queryset.model.RECORD_TYPE
        queryset = _filter_records(record_type, self.get_queryset(), request.query_params)
        if request.query_params.get("export") == "csv":
            return _csv_response(record_type, queryset)

        page = _positive_int(request.query_params.get("page"), 1)
        page_size = min(_positive_int(request.query_params.get("page_size"), 25), 100)
        cache_key = tenant_cache_key(
            request.user.tenant_id,
            f"{record_type}-list-v2",
            request.META.get("QUERY_STRING", "default") or "default",
        )
        cached = get_cached(cache_key)
        if cached is not None:
            return Response(cached)

        total_count = queryset.count()
        start = (page - 1) * page_size
        data = {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "results": _record_list_data(record_type, queryset[start : start + page_size]),
        }
        set_cached(cache_key, data)
        return Response(data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        record = self.get_object()
        if record.locked:
            raise ValidationError("Approved records are locked and cannot be edited.")

        before = _record_details(record)
        serializer = self.get_serializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()

        update_fields = []
        if isinstance(record, FuelRecord):
            record.unit = (record.unit or "").upper()
            factor = services.FUEL_UNIT_FACTORS.get(record.unit, Decimal("1"))
            record.normalized_quantity = (record.quantity * factor).quantize(Decimal("0.001"))
            update_fields.extend(["unit", "normalized_quantity"])

        if record.status != RecordStatus.PENDING:
            record.status = RecordStatus.PENDING
            record.locked = False
            update_fields.extend(["status", "locked"])

        if update_fields:
            record.save(update_fields=update_fields)

        from apps.validation_service.services import validate_record

        validate_record(record)
        create_audit_log(
            AuditLog.Action.EDIT,
            record,
            request.user,
            details={
                "before": before,
                "after": _record_details(record),
            },
        )
        transaction.on_commit(lambda: bump_tenant_cache_version(request.user.tenant_id))
        return Response(self.get_serializer(record).data)

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        if record.locked:
            raise ValidationError("Approved records are locked and cannot be deleted.")

        from apps.validation_service.models import ValidationIssue

        ValidationIssue.objects.filter(record_type=record.RECORD_TYPE, record_id=record.id).delete()
        create_audit_log(
            AuditLog.Action.DELETE,
            record,
            request.user,
            details={
                "status": record.status,
                "source_file": record.datasource.filename,
            },
        )
        record.delete()
        bump_tenant_cache_version(request.user.tenant_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FuelRecordViewSet(
    TenantRecordViewSetMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = FuelRecord.objects.all()
    serializer_class = FuelRecordSerializer


class ElectricityRecordViewSet(
    TenantRecordViewSetMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ElectricityRecord.objects.all()
    serializer_class = ElectricityRecordSerializer


class TravelRecordViewSet(
    TenantRecordViewSetMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = TravelRecord.objects.all()
    serializer_class = TravelRecordSerializer


def _choice_value(value):
    return value.value if hasattr(value, "value") else value


def _upload_job_data(job):
    return {
        "upload_job_id": job.id,
        "source_type": job.source_type,
        "filename": job.original_filename,
        "status": job.status,
        "total_records": job.total_records,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }


def _filter_records(record_type, queryset, params):
    status_filter = params.get("status")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    source_file = params.get("source_file")
    if source_file:
        queryset = queryset.filter(datasource__filename__icontains=source_file)

    date_field = DATE_FIELD_BY_RECORD_TYPE[record_type]
    if params.get("date_from"):
        queryset = queryset.filter(**{f"{date_field}__gte": params["date_from"]})
    if params.get("date_to"):
        queryset = queryset.filter(**{f"{date_field}__lte": params["date_to"]})

    severity = params.get("severity")
    if severity:
        record_ids = ValidationIssue.objects.filter(record_type=record_type, severity=severity).values("record_id")
        queryset = queryset.filter(id__in=record_ids)

    search = params.get("search")
    if search:
        search_query = Q()
        for field in SEARCH_FIELDS_BY_RECORD_TYPE[record_type]:
            search_query |= Q(**{f"{field}__icontains": search})
        queryset = queryset.filter(search_query)

    return queryset.distinct()


def _record_list_data(record_type, queryset):
    records = list(queryset)
    fields = LIST_FIELDS_BY_RECORD_TYPE[record_type]
    issue_lookup = _issue_lookup(record_type, [record.id for record in records])
    return [
        {
            **{field: _json_value(getattr(record, field)) for field in fields},
            "issues": issue_lookup.get(record.id, []),
        }
        for record in records
    ]


def _csv_response(record_type, queryset):
    fields = LIST_FIELDS_BY_RECORD_TYPE[record_type]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{record_type.lower()}-records.csv"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for row in _record_list_data(record_type, queryset):
        writer.writerow([row.get(field, "") for field in fields])
    return response


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _issue_lookup(record_type, record_ids):
    issues_by_record = {}
    issues = ValidationIssue.objects.filter(record_type=record_type, record_id__in=record_ids).order_by(
        "severity",
        "created_at",
    )
    for issue in ValidationIssueSerializer(issues, many=True).data:
        issues_by_record.setdefault(issue["record_id"], []).append(issue)
    return issues_by_record


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _record_details(record):
    if isinstance(record, FuelRecord):
        return {
            "date": record.date.isoformat() if record.date else None,
            "plant_code": record.plant_code,
            "fuel_type": record.fuel_type,
            "quantity": str(record.quantity),
            "unit": record.unit,
            "normalized_quantity": str(record.normalized_quantity),
            "status": record.status,
        }
    if isinstance(record, ElectricityRecord):
        return {
            "meter_id": record.meter_id,
            "billing_start": record.billing_start.isoformat() if record.billing_start else None,
            "billing_end": record.billing_end.isoformat() if record.billing_end else None,
            "kwh": str(record.kwh),
            "status": record.status,
        }
    return {
        "trip_type": record.trip_type,
        "origin": record.origin,
        "destination": record.destination,
        "distance_km": str(record.distance_km),
        "status": record.status,
    }
