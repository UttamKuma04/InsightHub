from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.cache import get_cached, set_cached, tenant_cache_key
from apps.core.permissions import IsAnalystOrAdmin
from apps.ingestion.models import DataSource, ElectricityRecord, FuelRecord, RecordStatus, TravelRecord
from apps.validation_service.models import ValidationIssue


class DashboardSummaryView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        tenant = request.user.tenant
        cache_key = tenant_cache_key(tenant.id, "dashboard-summary")
        cached = get_cached(cache_key)
        if cached is not None:
            return Response(cached)

        fuel = FuelRecord.objects.filter(datasource__tenant=tenant)
        electricity = ElectricityRecord.objects.filter(datasource__tenant=tenant)
        travel = TravelRecord.objects.filter(datasource__tenant=tenant)

        issue_scope = (
            Q(record_type=FuelRecord.RECORD_TYPE, record_id__in=fuel.values("id"))
            | Q(record_type=ElectricityRecord.RECORD_TYPE, record_id__in=electricity.values("id"))
            | Q(record_type=TravelRecord.RECORD_TYPE, record_id__in=travel.values("id"))
        )

        data = {
            "total_uploads": DataSource.objects.filter(tenant=tenant).count(),
            "total_fuel_records": fuel.count(),
            "total_electricity_records": electricity.count(),
            "total_travel_records": travel.count(),
            "pending_reviews": _status_count(fuel, electricity, travel, RecordStatus.PENDING),
            "approved_records": _status_count(fuel, electricity, travel, RecordStatus.APPROVED),
            "rejected_records": _status_count(fuel, electricity, travel, RecordStatus.REJECTED),
            "validation_warnings": ValidationIssue.objects.filter(
                issue_scope,
                severity=ValidationIssue.Severity.WARNING,
            ).count(),
            "validation_errors": ValidationIssue.objects.filter(
                issue_scope,
                severity=ValidationIssue.Severity.ERROR,
            ).count(),
        }
        set_cached(cache_key, data)
        return Response(data)


class DashboardDrilldownView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        metric = request.query_params.get("metric")
        tenant = request.user.tenant
        cache_key = tenant_cache_key(tenant.id, "dashboard-drilldown", metric or "missing")
        cached = get_cached(cache_key)
        if cached is not None:
            return Response(cached)

        if metric == "total_uploads":
            data = _upload_rows(tenant)
            set_cached(cache_key, data)
            return Response(data)
        if metric == "total_fuel_records":
            data = _record_rows("Fuel Records", FuelRecord.objects.filter(datasource__tenant=tenant))
            set_cached(cache_key, data)
            return Response(data)
        if metric == "total_electricity_records":
            data = _record_rows("Electricity Records", ElectricityRecord.objects.filter(datasource__tenant=tenant))
            set_cached(cache_key, data)
            return Response(data)
        if metric == "total_travel_records":
            data = _record_rows("Travel Records", TravelRecord.objects.filter(datasource__tenant=tenant))
            set_cached(cache_key, data)
            return Response(data)
        if metric == "pending_reviews":
            data = _status_rows(tenant, RecordStatus.PENDING, "Pending Reviews")
            set_cached(cache_key, data)
            return Response(data)
        if metric == "approved_records":
            data = _status_rows(tenant, RecordStatus.APPROVED, "Approved Records")
            set_cached(cache_key, data)
            return Response(data)
        if metric == "rejected_records":
            data = _status_rows(tenant, RecordStatus.REJECTED, "Rejected Records")
            set_cached(cache_key, data)
            return Response(data)
        if metric == "validation_warnings":
            data = _issue_rows(tenant, ValidationIssue.Severity.WARNING, "Validation Warnings")
            set_cached(cache_key, data)
            return Response(data)
        if metric == "validation_errors":
            data = _issue_rows(tenant, ValidationIssue.Severity.ERROR, "Validation Errors")
            set_cached(cache_key, data)
            return Response(data)

        raise ValidationError("Unsupported dashboard metric.")


def _status_count(fuel, electricity, travel, status):
    return (
        fuel.filter(status=status).count()
        + electricity.filter(status=status).count()
        + travel.filter(status=status).count()
    )


def _upload_rows(tenant):
    uploads = DataSource.objects.filter(tenant=tenant).select_related("uploaded_by")
    return {
        "title": "Total Uploads",
        "columns": [
            {"key": "id", "label": "ID"},
            {"key": "source_type", "label": "Source"},
            {"key": "filename", "label": "Filename"},
            {"key": "uploaded_by", "label": "Uploaded By"},
            {"key": "uploaded_at", "label": "Uploaded At"},
        ],
        "rows": [
            {
                "id": upload.id,
                "source_type": upload.source_type,
                "filename": upload.filename,
                "uploaded_by": upload.uploaded_by.email,
                "uploaded_at": upload.uploaded_at,
            }
            for upload in uploads
        ],
    }


def _status_rows(tenant, status, title):
    records = []
    for queryset in _tenant_record_querysets(tenant):
        records.extend(queryset.filter(status=status))
    return _record_rows_from_list(title, records)


def _record_rows(title, queryset):
    return _record_rows_from_list(title, queryset.select_related("datasource"))


def _record_rows_from_list(title, records):
    return {
        "title": title,
        "columns": [
            {"key": "record_type", "label": "Type"},
            {"key": "record_id", "label": "Record ID"},
            {"key": "summary", "label": "Summary"},
            {"key": "status", "label": "Status"},
            {"key": "locked", "label": "Locked"},
            {"key": "source_file", "label": "Source File"},
        ],
        "rows": [
            {
                "record_type": record.RECORD_TYPE,
                "record_id": record.id,
                "summary": _record_summary(record),
                "status": record.status,
                "locked": "Yes" if record.locked else "No",
                "source_file": record.datasource.filename,
            }
            for record in records
        ],
    }


def _issue_rows(tenant, severity, title):
    fuel = FuelRecord.objects.filter(datasource__tenant=tenant).select_related("datasource")
    electricity = ElectricityRecord.objects.filter(datasource__tenant=tenant).select_related("datasource")
    travel = TravelRecord.objects.filter(datasource__tenant=tenant).select_related("datasource")
    issue_scope = (
        Q(record_type=FuelRecord.RECORD_TYPE, record_id__in=fuel.values("id"))
        | Q(record_type=ElectricityRecord.RECORD_TYPE, record_id__in=electricity.values("id"))
        | Q(record_type=TravelRecord.RECORD_TYPE, record_id__in=travel.values("id"))
    )
    record_lookup = {
        FuelRecord.RECORD_TYPE: {record.id: record for record in fuel},
        ElectricityRecord.RECORD_TYPE: {record.id: record for record in electricity},
        TravelRecord.RECORD_TYPE: {record.id: record for record in travel},
    }
    issues = ValidationIssue.objects.filter(issue_scope, severity=severity).order_by("-created_at")

    return {
        "title": title,
        "columns": [
            {"key": "record_type", "label": "Type"},
            {"key": "record_id", "label": "Record ID"},
            {"key": "severity", "label": "Severity"},
            {"key": "message", "label": "Message"},
            {"key": "summary", "label": "Record"},
            {"key": "source_file", "label": "Source File"},
            {"key": "created_at", "label": "Created At"},
        ],
        "rows": [
            _issue_row(issue, record_lookup.get(issue.record_type, {}).get(issue.record_id))
            for issue in issues
        ],
    }


def _issue_row(issue, record):
    return {
        "record_type": issue.record_type,
        "record_id": issue.record_id,
        "severity": issue.severity,
        "message": issue.message,
        "summary": _record_summary(record) if record else "Record deleted",
        "source_file": record.datasource.filename if record else "-",
        "created_at": issue.created_at,
    }


def _tenant_record_querysets(tenant):
    return [
        FuelRecord.objects.filter(datasource__tenant=tenant).select_related("datasource"),
        ElectricityRecord.objects.filter(datasource__tenant=tenant).select_related("datasource"),
        TravelRecord.objects.filter(datasource__tenant=tenant).select_related("datasource"),
    ]


def _record_summary(record):
    if isinstance(record, FuelRecord):
        return f"{record.ebeln}/{record.ebelp} · {record.matnr or record.fuel_type} · {record.quantity} {record.unit}"
    if isinstance(record, ElectricityRecord):
        return f"{record.account_no} · {record.meter_id} · {record.billing_start} to {record.billing_end} · {record.kwh} {record.consumption_unit or 'kWh'}"
    if isinstance(record, TravelRecord):
        route = f"{record.origin or '-'} to {record.destination or '-'}"
        return f"{record.report_id} · {record.expense_type} · {route} · {record.amount or '-'} {record.currency}"
    return "-"
