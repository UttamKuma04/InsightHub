from rest_framework import serializers
from django.conf import settings

from apps.ingestion.models import DataSource, ElectricityRecord, FuelRecord, TravelRecord


class UploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        filename = getattr(file, "name", "").lower()
        content_type = getattr(file, "content_type", "")
        if not filename.endswith(".csv") and content_type not in ("text/csv", "application/vnd.ms-excel"):
            raise serializers.ValidationError("Only CSV files are allowed.")
        if file.size > settings.UPLOAD_MAX_BYTES:
            raise serializers.ValidationError("CSV file is too large.")
        return file


class DataSourceSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.EmailField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = DataSource
        fields = ("id", "source_type", "filename", "uploaded_by", "uploaded_at")


class RecordIssueMixin:
    def get_issues(self, obj):
        from apps.validation_service.models import ValidationIssue
        from apps.validation_service.serializers import ValidationIssueSerializer

        issues = ValidationIssue.objects.filter(
            record_type=obj.RECORD_TYPE,
            record_id=obj.id,
        ).order_by("severity", "created_at")
        return ValidationIssueSerializer(issues, many=True).data


class FuelRecordSerializer(RecordIssueMixin, serializers.ModelSerializer):
    datasource = DataSourceSerializer(read_only=True)
    issues = serializers.SerializerMethodField()

    class Meta:
        model = FuelRecord
        fields = (
            "id",
            "datasource",
            "source_payload",
            "ebeln",
            "ebelp",
            "bsart",
            "bstyp",
            "statu",
            "aedat",
            "bedat",
            "lifnr",
            "vendor_name",
            "ekorg",
            "ekgrp",
            "waers",
            "wkurs",
            "matnr",
            "txz01",
            "matkl",
            "werks",
            "lgort",
            "date",
            "plant_code",
            "fuel_type",
            "quantity",
            "unit",
            "normalized_quantity",
            "netpr",
            "netwr",
            "bwart",
            "budat",
            "mblnr",
            "mjahr",
            "zeile",
            "kostl",
            "aufnr",
            "inco1",
            "zterms",
            "loekz",
            "section_source",
            "status",
            "locked",
            "issues",
        )
        read_only_fields = ("datasource", "normalized_quantity", "status", "locked", "issues")


class ElectricityRecordSerializer(RecordIssueMixin, serializers.ModelSerializer):
    datasource = DataSourceSerializer(read_only=True)
    issues = serializers.SerializerMethodField()

    class Meta:
        model = ElectricityRecord
        fields = (
            "id",
            "datasource",
            "source_payload",
            "account_no",
            "meter_id",
            "site_name",
            "address",
            "city",
            "state",
            "discom",
            "tariff_category",
            "tariff_code",
            "supply_voltage",
            "hv_lv",
            "contracted_demand_kva",
            "billing_start",
            "billing_end",
            "billing_days",
            "bill_date",
            "due_date",
            "meter_read_start",
            "meter_read_end",
            "read_type",
            "kwh",
            "consumption_unit",
            "peak_kwh",
            "offpeak_kwh",
            "shoulder_kwh",
            "max_demand",
            "demand_unit",
            "power_factor",
            "supply_charge_inr",
            "energy_charge_inr",
            "demand_charge_inr",
            "pf_penalty_inr",
            "regulatory_charge_inr",
            "electricity_duty_inr",
            "total_bill_inr",
            "currency",
            "bill_reference",
            "payment_status",
            "status",
            "locked",
            "issues",
        )
        read_only_fields = ("datasource", "status", "locked", "issues")


class TravelRecordSerializer(RecordIssueMixin, serializers.ModelSerializer):
    datasource = DataSourceSerializer(read_only=True)
    issues = serializers.SerializerMethodField()

    class Meta:
        model = TravelRecord
        fields = (
            "id",
            "datasource",
            "source_payload",
            "report_id",
            "expense_type",
            "transaction_date",
            "employee_id",
            "employee_name",
            "department",
            "cost_center",
            "job_title",
            "home_city",
            "trip_purpose",
            "payment_method",
            "origin_iata",
            "destination_iata",
            "origin_city",
            "destination_city",
            "trip_type",
            "origin",
            "destination",
            "distance_km",
            "airline_code",
            "airline_name",
            "flight_number",
            "cabin_class",
            "hotel_name",
            "hotel_city",
            "check_in_date",
            "check_out_date",
            "ground_transport_type",
            "amount",
            "currency",
            "reimbursable",
            "policy_compliant",
            "policy_exception_reason",
            "emission_factor",
            "estimated_emissions_kgco2e",
            "approval_status",
            "receipt_attached",
            "notes",
            "status",
            "locked",
            "issues",
        )
        read_only_fields = ("datasource", "status", "locked", "issues")
