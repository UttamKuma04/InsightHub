from django.conf import settings
from django.db import models


class RecordStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class DataSource(models.Model):
    class SourceType(models.TextChoices):
        SAP = "SAP", "SAP"
        UTILITY = "UTILITY", "Utility"
        TRAVEL = "TRAVEL", "Travel"

    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="data_sources")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "data_sources"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["tenant", "source_type"], name="data_source_tenant_source_idx"),
        ]

    def __str__(self):
        return f"{self.source_type}: {self.filename}"


class UploadJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="upload_jobs")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="upload_jobs")
    source_type = models.CharField(max_length=20, choices=DataSource.SourceType.choices)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    total_records = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "upload_jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"], name="upload_job_tenant_status_idx"),
        ]

    def __str__(self):
        return f"{self.source_type} upload {self.id} ({self.status})"


class FuelRecord(models.Model):
    RECORD_TYPE = "FUEL"

    datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="fuel_records")
    source_payload = models.JSONField(default=dict, blank=True)

    ebeln = models.CharField(max_length=30, blank=True)
    ebelp = models.CharField(max_length=10, blank=True)
    bsart = models.CharField(max_length=20, blank=True)
    bstyp = models.CharField(max_length=10, blank=True)
    statu = models.CharField(max_length=10, blank=True)
    aedat = models.DateField(null=True, blank=True)
    bedat = models.DateField(null=True, blank=True)
    lifnr = models.CharField(max_length=30, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)
    ekorg = models.CharField(max_length=20, blank=True)
    ekgrp = models.CharField(max_length=20, blank=True)
    waers = models.CharField(max_length=10, blank=True)
    wkurs = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    matnr = models.CharField(max_length=100, blank=True)
    txz01 = models.CharField(max_length=255, blank=True)
    matkl = models.CharField(max_length=50, blank=True)
    werks = models.CharField(max_length=100, blank=True)
    lgort = models.CharField(max_length=50, blank=True)
    date = models.DateField(null=True, blank=True)
    plant_code = models.CharField(max_length=100, blank=True)
    fuel_type = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    netpr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    netwr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    bwart = models.CharField(max_length=10, blank=True)
    budat = models.DateField(null=True, blank=True)
    mblnr = models.CharField(max_length=30, blank=True)
    mjahr = models.CharField(max_length=10, blank=True)
    zeile = models.CharField(max_length=10, blank=True)
    kostl = models.CharField(max_length=50, blank=True)
    aufnr = models.CharField(max_length=50, blank=True)
    inco1 = models.CharField(max_length=20, blank=True)
    zterms = models.CharField(max_length=20, blank=True)
    loekz = models.CharField(max_length=10, blank=True)
    section_source = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    locked = models.BooleanField(default=False)

    class Meta:
        db_table = "fuel_records"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status", "locked"], name="fuel_record_status_locked_idx"),
        ]

    def __str__(self):
        return f"Fuel {self.id} ({self.status})"


class ElectricityRecord(models.Model):
    RECORD_TYPE = "ELECTRICITY"

    datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="electricity_records")
    source_payload = models.JSONField(default=dict, blank=True)
    account_no = models.CharField(max_length=100, blank=True)
    meter_id = models.CharField(max_length=100, blank=True)
    site_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    discom = models.CharField(max_length=100, blank=True)
    tariff_category = models.CharField(max_length=100, blank=True)
    tariff_code = models.CharField(max_length=100, blank=True)
    supply_voltage = models.CharField(max_length=50, blank=True)
    hv_lv = models.CharField(max_length=20, blank=True)
    contracted_demand_kva = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    billing_start = models.DateField(null=True, blank=True)
    billing_end = models.DateField(null=True, blank=True)
    billing_days = models.IntegerField(null=True, blank=True)
    bill_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    meter_read_start = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    meter_read_end = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    read_type = models.CharField(max_length=20, blank=True)
    kwh = models.DecimalField(max_digits=14, decimal_places=3)
    consumption_unit = models.CharField(max_length=20, blank=True)
    peak_kwh = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    offpeak_kwh = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    shoulder_kwh = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    max_demand = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    demand_unit = models.CharField(max_length=20, blank=True)
    power_factor = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    supply_charge_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    energy_charge_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    demand_charge_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    pf_penalty_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    regulatory_charge_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    electricity_duty_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    total_bill_inr = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    bill_reference = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    locked = models.BooleanField(default=False)

    class Meta:
        db_table = "electricity_records"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status", "locked"], name="electricity_status_locked_idx"),
        ]

    def __str__(self):
        return f"Electricity {self.id} ({self.status})"


class TravelRecord(models.Model):
    RECORD_TYPE = "TRAVEL"

    datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="travel_records")
    source_payload = models.JSONField(default=dict, blank=True)
    report_id = models.CharField(max_length=100, blank=True)
    expense_type = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateField(null=True, blank=True)
    employee_id = models.CharField(max_length=100, blank=True)
    employee_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    home_city = models.CharField(max_length=100, blank=True)
    trip_purpose = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(max_length=100, blank=True)
    origin_iata = models.CharField(max_length=10, blank=True)
    destination_iata = models.CharField(max_length=10, blank=True)
    origin_city = models.CharField(max_length=100, blank=True)
    destination_city = models.CharField(max_length=100, blank=True)
    trip_type = models.CharField(max_length=100, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=100, blank=True)
    distance_km = models.DecimalField(max_digits=14, decimal_places=3)
    airline_code = models.CharField(max_length=20, blank=True)
    airline_name = models.CharField(max_length=100, blank=True)
    flight_number = models.CharField(max_length=30, blank=True)
    cabin_class = models.CharField(max_length=50, blank=True)
    hotel_name = models.CharField(max_length=255, blank=True)
    hotel_city = models.CharField(max_length=100, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    ground_transport_type = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    reimbursable = models.CharField(max_length=20, blank=True)
    policy_compliant = models.CharField(max_length=20, blank=True)
    policy_exception_reason = models.TextField(blank=True)
    emission_factor = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    estimated_emissions_kgco2e = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    approval_status = models.CharField(max_length=50, blank=True)
    receipt_attached = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    locked = models.BooleanField(default=False)

    class Meta:
        db_table = "travel_records"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status", "locked"], name="travel_status_locked_idx"),
        ]

    def __str__(self):
        return f"Travel {self.id} ({self.status})"
