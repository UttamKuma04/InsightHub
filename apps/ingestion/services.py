import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.audit.models import AuditLog
from apps.audit.services import create_audit_logs
from apps.ingestion.models import DataSource, ElectricityRecord, FuelRecord, TravelRecord
from apps.validation_service.services import validate_records


DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y%m%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%d-%b-%y",
    "%d-%b-%Y",
)

SAP_FIELD_ALIASES = {
    "ebeln": ("ebeln",),
    "ebelp": ("ebelp",),
    "bsart": ("bsart",),
    "bstyp": ("bstyp",),
    "statu": ("statu",),
    "aedat": ("aedat",),
    "bedat": ("bedat",),
    "lifnr": ("lifnr",),
    "vendor_name": ("vendor_name", "name1"),
    "ekorg": ("ekorg",),
    "ekgrp": ("ekgrp",),
    "waers": ("waers",),
    "wkurs": ("wkurs",),
    "matnr": ("matnr",),
    "txz01": ("txz01", "maktx", "fuel_type", "fuel type"),
    "matkl": ("matkl",),
    "werks": ("werks", "plant_code", "plant code"),
    "lgort": ("lgort",),
    "quantity": ("menge", "quantity"),
    "unit": ("meins", "unit"),
    "netpr": ("netpr",),
    "netwr": ("netwr",),
    "bwart": ("bwart",),
    "budat": ("budat", "date"),
    "mblnr": ("mblnr",),
    "mjahr": ("mjahr",),
    "zeile": ("zeile",),
    "kostl": ("kostl",),
    "aufnr": ("aufnr",),
    "inco1": ("inco1",),
    "zterms": ("zterms",),
    "loekz": ("loekz",),
    "section_source": ("section_source",),
}

UTILITY_FIELD_ALIASES = {
    "account_no": ("account_no", "account number"),
    "meter_id": ("meter_id", "meter id"),
    "site_name": ("site_name", "account name"),
    "address": ("address", "service address"),
    "city": ("city",),
    "state": ("state",),
    "discom": ("discom",),
    "tariff_category": ("tariff_category",),
    "tariff_code": ("tariff_code", "tariff code"),
    "supply_voltage": ("supply_voltage",),
    "hv_lv": ("hv_lv",),
    "contracted_demand_kva": ("contracted_demand_kva",),
    "billing_start": ("period_start", "billing_start", "billing period start"),
    "billing_end": ("period_end", "billing_end", "billing period end"),
    "billing_days": ("billing_days", "days in period"),
    "bill_date": ("bill_date",),
    "due_date": ("due_date",),
    "meter_read_start": ("meter_read_start", "meter read start (kwh)"),
    "meter_read_end": ("meter_read_end", "meter read end (kwh)"),
    "read_type": ("read_type", "read type"),
    "kwh": ("consumption", "kwh", "consumption (kwh)"),
    "consumption_unit": ("consumption_unit",),
    "peak_kwh": ("peak_kwh", "on-peak consumption (kwh)"),
    "offpeak_kwh": ("offpeak_kwh", "off-peak consumption (kwh)"),
    "shoulder_kwh": ("shoulder_kwh",),
    "max_demand": ("max_demand", "peak demand (kw)"),
    "demand_unit": ("demand_unit",),
    "power_factor": ("power_factor",),
    "supply_charge_inr": ("supply_charge_inr", "supply charge (gbp)"),
    "energy_charge_inr": ("energy_charge_inr", "distribution charge (gbp)"),
    "demand_charge_inr": ("demand_charge_inr", "demand charge (gbp)"),
    "pf_penalty_inr": ("pf_penalty_inr",),
    "regulatory_charge_inr": ("regulatory_charge_inr", "climate levy (gbp)"),
    "electricity_duty_inr": ("electricity_duty_inr", "vat (gbp)"),
    "total_bill_inr": ("total_bill_inr", "total billed (gbp)"),
    "currency": ("currency",),
    "bill_reference": ("bill_reference",),
    "payment_status": ("payment_status",),
}

TRAVEL_FIELD_ALIASES = {
    "report_id": ("report_id",),
    "expense_type": ("expense_type", "travel_type", "trip_type"),
    "transaction_date": ("transaction_date", "travel_date_start", "booking_date"),
    "employee_id": ("employee_id",),
    "employee_name": ("employee_name",),
    "department": ("department",),
    "cost_center": ("cost_center",),
    "job_title": ("job_title",),
    "home_city": ("home_city",),
    "trip_purpose": ("trip_purpose",),
    "payment_method": ("payment_method",),
    "origin_iata": ("origin_iata", "origin"),
    "destination_iata": ("destination_iata", "destination"),
    "origin_city": ("origin_city",),
    "destination_city": ("destination_city",),
    "distance_km": ("distance_km",),
    "airline_code": ("airline_code", "carrier_vendor"),
    "airline_name": ("airline_name",),
    "flight_number": ("flight_number",),
    "cabin_class": ("cabin_class",),
    "hotel_name": ("hotel_name",),
    "hotel_city": ("hotel_city",),
    "check_in_date": ("check_in_date",),
    "check_out_date": ("check_out_date",),
    "ground_transport_type": ("ground_transport_type",),
    "amount": ("amount",),
    "currency": ("currency",),
    "reimbursable": ("reimbursable",),
    "policy_compliant": ("policy_compliant",),
    "policy_exception_reason": ("policy_exception_reason",),
    "emission_factor": ("emission_factor_kgco2e_per_km_or_night",),
    "estimated_emissions_kgco2e": ("estimated_emissions_kgco2e",),
    "approval_status": ("approval_status",),
    "receipt_attached": ("receipt_attached",),
    "notes": ("notes",),
}

FUEL_UNIT_FACTORS = {
    "GAL": Decimal("3.785"),
    "GALLON": Decimal("3.785"),
    "GALLONS": Decimal("3.785"),
    "L": Decimal("1"),
    "LTR": Decimal("1"),
    "LITER": Decimal("1"),
    "LITRE": Decimal("1"),
    "LITERS": Decimal("1"),
    "LITRES": Decimal("1"),
    "KL": Decimal("1000"),
    "M3": Decimal("1000"),
    "KG": Decimal("1"),
    "TO": Decimal("1"),
    "MT": Decimal("1"),
}


def ingest_sap_fuel_csv(uploaded_file, user):
    rows = _read_csv(uploaded_file, SAP_FIELD_ALIASES)
    return _create_records(uploaded_file, user, DataSource.SourceType.SAP, rows, _build_fuel_record)


def ingest_utility_csv(uploaded_file, user):
    rows = _read_csv(uploaded_file, UTILITY_FIELD_ALIASES)
    return _create_records(uploaded_file, user, DataSource.SourceType.UTILITY, rows, _build_electricity_record)


def ingest_travel_csv(uploaded_file, user):
    rows = _read_csv(uploaded_file, TRAVEL_FIELD_ALIASES)
    return _create_records(uploaded_file, user, DataSource.SourceType.TRAVEL, rows, _build_travel_record)


def _create_records(uploaded_file, user, source_type, rows, record_builder, chunk_size=500):
    if not getattr(user, "tenant_id", None):
        raise ValidationError("Authenticated user must belong to a tenant.")

    datasource = DataSource.objects.create(
        tenant=user.tenant,
        source_type=source_type,
        filename=getattr(uploaded_file, "name", "upload.csv"),
        uploaded_by=user,
    )

    records = []
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        chunk_records = [record_builder(datasource, row) for row in chunk]
        if not chunk_records:
            continue

        with transaction.atomic():
            created_records = chunk_records[0].__class__.objects.bulk_create(
                chunk_records,
                batch_size=chunk_size,
            )
            validate_records(created_records)
            create_audit_logs(
                AuditLog.Action.CREATE,
                created_records,
                user,
                details_factory=lambda record: {"source_file": record.datasource.filename},
            )
            records.extend(created_records)

    return datasource, records


def _read_csv(uploaded_file, field_aliases):
    try:
        decoded = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("CSV must be UTF-8 encoded.") from exc

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValidationError("CSV must include a header row.")

    header_lookup = {
        _normalize_header(header): header
        for header in reader.fieldnames
        if header and header.strip()
    }
    matched_headers = {
        canonical_field: _find_source_header(header_lookup, aliases)
        for canonical_field, aliases in field_aliases.items()
    }

    normalized_rows = []
    for raw_row in reader:
        source_payload = {
            key.strip(): (value or "").strip()
            for key, value in raw_row.items()
            if key and key.strip()
        }
        row = {"source_payload": source_payload}
        for canonical_field, source_header in matched_headers.items():
            row[canonical_field] = (raw_row.get(source_header) or "").strip() if source_header else ""
        normalized_rows.append(row)
    return normalized_rows


def _build_fuel_record(datasource, row):
    quantity = _to_decimal(row.get("quantity")) or Decimal("0.000")
    unit = (row.get("unit") or "").upper()
    factor = FUEL_UNIT_FACTORS.get(unit, Decimal("1"))
    budat = _parse_date(row.get("budat"))
    bedat = _parse_date(row.get("bedat"))
    txz01 = row.get("txz01", "")
    matnr = row.get("matnr", "")
    werks = row.get("werks", "")

    return FuelRecord(
        datasource=datasource,
        source_payload=row["source_payload"],
        ebeln=row.get("ebeln", ""),
        ebelp=row.get("ebelp", ""),
        bsart=row.get("bsart", ""),
        bstyp=row.get("bstyp", ""),
        statu=row.get("statu", ""),
        aedat=_parse_date(row.get("aedat")),
        bedat=bedat,
        lifnr=row.get("lifnr", ""),
        vendor_name=row.get("vendor_name", ""),
        ekorg=row.get("ekorg", ""),
        ekgrp=row.get("ekgrp", ""),
        waers=row.get("waers", ""),
        wkurs=_to_decimal(row.get("wkurs"), places="0.0001"),
        matnr=matnr,
        txz01=txz01,
        matkl=row.get("matkl", ""),
        werks=werks,
        lgort=row.get("lgort", ""),
        date=budat or bedat,
        plant_code=werks,
        fuel_type=txz01 or matnr,
        quantity=quantity,
        unit=unit,
        normalized_quantity=(quantity * factor).quantize(Decimal("0.001")),
        netpr=_to_decimal(row.get("netpr")),
        netwr=_to_decimal(row.get("netwr")),
        bwart=row.get("bwart", ""),
        budat=budat,
        mblnr=row.get("mblnr", ""),
        mjahr=row.get("mjahr", ""),
        zeile=row.get("zeile", ""),
        kostl=row.get("kostl", ""),
        aufnr=row.get("aufnr", ""),
        inco1=row.get("inco1", ""),
        zterms=row.get("zterms", ""),
        loekz=row.get("loekz", ""),
        section_source=row.get("section_source", ""),
    )


def _build_electricity_record(datasource, row):
    consumption = _to_decimal(row.get("kwh")) or Decimal("0.000")
    return ElectricityRecord(
        datasource=datasource,
        source_payload=row["source_payload"],
        account_no=row.get("account_no", ""),
        meter_id=row.get("meter_id", ""),
        site_name=row.get("site_name", ""),
        address=row.get("address", ""),
        city=row.get("city", ""),
        state=row.get("state", ""),
        discom=row.get("discom", ""),
        tariff_category=row.get("tariff_category", ""),
        tariff_code=row.get("tariff_code", ""),
        supply_voltage=row.get("supply_voltage", ""),
        hv_lv=row.get("hv_lv", ""),
        contracted_demand_kva=_to_decimal(row.get("contracted_demand_kva")),
        billing_start=_parse_date(row.get("billing_start")),
        billing_end=_parse_date(row.get("billing_end")),
        billing_days=_to_int(row.get("billing_days")),
        bill_date=_parse_date(row.get("bill_date")),
        due_date=_parse_date(row.get("due_date")),
        meter_read_start=_to_decimal(row.get("meter_read_start")),
        meter_read_end=_to_decimal(row.get("meter_read_end")),
        read_type=(row.get("read_type") or "").upper(),
        kwh=consumption,
        consumption_unit=row.get("consumption_unit", "") or "kWh",
        peak_kwh=_to_decimal(row.get("peak_kwh")),
        offpeak_kwh=_to_decimal(row.get("offpeak_kwh")),
        shoulder_kwh=_to_decimal(row.get("shoulder_kwh")),
        max_demand=_to_decimal(row.get("max_demand")),
        demand_unit=row.get("demand_unit", ""),
        power_factor=_to_decimal(row.get("power_factor")),
        supply_charge_inr=_to_decimal(row.get("supply_charge_inr")),
        energy_charge_inr=_to_decimal(row.get("energy_charge_inr")),
        demand_charge_inr=_to_decimal(row.get("demand_charge_inr")),
        pf_penalty_inr=_to_decimal(row.get("pf_penalty_inr")),
        regulatory_charge_inr=_to_decimal(row.get("regulatory_charge_inr")),
        electricity_duty_inr=_to_decimal(row.get("electricity_duty_inr")),
        total_bill_inr=_to_decimal(row.get("total_bill_inr")),
        currency=row.get("currency", "") or "INR",
        bill_reference=row.get("bill_reference", ""),
        payment_status=row.get("payment_status", ""),
    )


def _build_travel_record(datasource, row):
    expense_type = row.get("expense_type", "")
    origin_iata = row.get("origin_iata", "")
    destination_iata = row.get("destination_iata", "")
    distance = _to_decimal(row.get("distance_km")) or Decimal("0.000")

    return TravelRecord(
        datasource=datasource,
        source_payload=row["source_payload"],
        report_id=row.get("report_id", ""),
        expense_type=expense_type,
        transaction_date=_parse_date(row.get("transaction_date")),
        employee_id=row.get("employee_id", ""),
        employee_name=row.get("employee_name", ""),
        department=row.get("department", ""),
        cost_center=row.get("cost_center", ""),
        job_title=row.get("job_title", ""),
        home_city=row.get("home_city", ""),
        trip_purpose=row.get("trip_purpose", ""),
        payment_method=row.get("payment_method", ""),
        origin_iata=origin_iata,
        destination_iata=destination_iata,
        origin_city=row.get("origin_city", ""),
        destination_city=row.get("destination_city", ""),
        trip_type=expense_type,
        origin=origin_iata or row.get("origin_city", ""),
        destination=destination_iata or row.get("destination_city", ""),
        distance_km=distance,
        airline_code=row.get("airline_code", ""),
        airline_name=row.get("airline_name", ""),
        flight_number=row.get("flight_number", ""),
        cabin_class=row.get("cabin_class", ""),
        hotel_name=row.get("hotel_name", ""),
        hotel_city=row.get("hotel_city", ""),
        check_in_date=_parse_date(row.get("check_in_date")),
        check_out_date=_parse_date(row.get("check_out_date")),
        ground_transport_type=row.get("ground_transport_type", ""),
        amount=_to_decimal(row.get("amount")),
        currency=row.get("currency", ""),
        reimbursable=row.get("reimbursable", ""),
        policy_compliant=row.get("policy_compliant", ""),
        policy_exception_reason=row.get("policy_exception_reason", ""),
        emission_factor=_to_decimal(row.get("emission_factor"), places="0.000001"),
        estimated_emissions_kgco2e=_to_decimal(row.get("estimated_emissions_kgco2e")),
        approval_status=row.get("approval_status", ""),
        receipt_attached=row.get("receipt_attached", ""),
        notes=row.get("notes", ""),
    )


def _to_decimal(value, places="0.001"):
    value = (value or "").strip()
    if value == "":
        return None

    if "," in value and "." not in value:
        value = value.replace(",", ".")
    else:
        value = value.replace(",", "")

    try:
        return Decimal(value).quantize(Decimal(places))
    except (InvalidOperation, ValueError):
        return None


def _to_int(value):
    decimal_value = _to_decimal(value)
    return int(decimal_value) if decimal_value is not None else None


def _parse_date(value):
    value = (value or "").strip()
    if not value:
        return None

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def _find_source_header(header_lookup, aliases):
    for alias in aliases:
        source_header = header_lookup.get(_normalize_header(alias))
        if source_header:
            return source_header
    return None


def _normalize_header(header):
    return " ".join((header or "").strip().lower().split())
