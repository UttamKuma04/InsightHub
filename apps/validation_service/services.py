import re
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.ingestion.models import ElectricityRecord, FuelRecord, TravelRecord
from apps.validation_service.models import ValidationIssue


SAP_REVERSAL_MOVEMENTS = {"102", "122", "551"}
SAP_FUEL_UNITS = {"KL", "TO", "MT", "L", "KG", "M3"}
KNOWN_FUEL_PREFIXES = ("HSD", "HFO", "KER", "MS", "DIESEL", "PETROL", "FUEL")
KNOWN_DISCOMS = {
    "BEST",
    "MSEDCL",
    "BESCOM",
    "TANGEDCO",
    "TATA POWER",
    "ADANI",
    "CESC",
    "BYPL",
    "BRPL",
    "TPDDL",
    "PGVCL",
    "DGVCL",
    "UGVCL",
    "MGVCL",
    "KSEB",
}


def validate_record(record):
    created_issues = validate_records([record])
    return created_issues


def validate_records(records):
    records = list(records)
    if not records:
        return []

    issue_scope = Q()
    for record_type, record_ids in _record_ids_by_type(records).items():
        issue_scope |= Q(record_type=record_type, record_id__in=record_ids)
    if issue_scope:
        ValidationIssue.objects.filter(issue_scope).delete()

    fuel_context = _fuel_validation_context(
        [record for record in records if isinstance(record, FuelRecord)]
    )
    issues = []
    for record in records:
        if isinstance(record, FuelRecord):
            record_issues = _validate_fuel(record, fuel_context)
        elif isinstance(record, ElectricityRecord):
            record_issues = _validate_electricity(record)
        elif isinstance(record, TravelRecord):
            record_issues = _validate_travel(record)
        else:
            record_issues = []

        issues.extend(
            ValidationIssue(
                record_type=record.RECORD_TYPE,
                record_id=record.id,
                severity=severity,
                message=message,
            )
            for severity, message in record_issues
        )

    return ValidationIssue.objects.bulk_create(issues) if issues else []


def _validate_fuel(record, context=None):
    issues = []
    today = timezone.localdate()

    _required(issues, record.ebeln, "SAP: EBELN PO number is required.")
    _required(issues, record.ebelp, "SAP: EBELP line item is required.")
    _required(issues, record.matnr, "SAP: MATNR material number is required for factor lookup.")
    _required(issues, record.unit, "SAP: MEINS unit of measure is required.")
    if _blank(_raw(record, "MENGE")):
        _add(issues, "ERROR", "SAP: MENGE quantity is required.")
    _required(issues, record.werks, "SAP: WERKS plant code is required for site attribution.")
    if _blank(record.lifnr) and record.bstyp == "F":
        _add(issues, "ERROR", "SAP: External PO has no LIFNR vendor code.")
    if _blank(_raw(record, "BEDAT")):
        _add(issues, "ERROR", "SAP: BEDAT document date is required.")
    if _blank(record.waers) and _positive(record.netpr):
        _add(issues, "WARNING", "SAP: NETPR is populated but WAERS currency is missing.")
    if _blank(record.bwart) and record.mblnr:
        _add(issues, "ERROR", "SAP: MBLNR material document exists but BWART movement type is missing.")

    for source_field, parsed_value in (("BEDAT", record.bedat), ("AEDAT", record.aedat), ("BUDAT", record.budat)):
        if _raw(record, source_field) and parsed_value is None:
            _add(issues, "ERROR", f"SAP: {source_field} cannot be parsed as a valid date.")

    if record.bedat and record.bedat > today + timedelta(days=30):
        _add(issues, "WARNING", "SAP: BEDAT document date is more than 30 days in the future.")
    if record.aedat and record.bedat and record.aedat < record.bedat:
        _add(issues, "WARNING", "SAP: AEDAT change date is earlier than BEDAT document date.")

    if record.quantity <= 0 and record.bwart not in SAP_REVERSAL_MOVEMENTS:
        _add(issues, "ERROR", "SAP: MENGE must be positive unless BWART is reversal/return/scrapping.")
    if record.quantity < 0 and record.bwart == "101":
        _add(issues, "ERROR", "SAP: Goods receipt BWART 101 cannot have negative MENGE.")
    if record.netpr is not None and record.netpr < 0:
        _add(issues, "ERROR", "SAP: NETPR unit price cannot be negative for a standard PO.")
    if record.netpr == 0 and record.matkl == "FUEL":
        _add(issues, "WARNING", "SAP: Zero-price fuel order requires review.")
    if record.netwr is not None and record.netpr is not None:
        expected = (record.quantity * record.netpr).quantize(Decimal("0.01"))
        if abs(record.netwr - expected) > Decimal("0.05"):
            _add(issues, "WARNING", "SAP: NETWR differs from round(MENGE x NETPR, 2) by more than 0.05.")
    if record.quantity > 500 and record.unit == "KL" and record.matkl == "FUEL":
        _add(issues, "WARNING", "SAP: Single fuel line exceeds 500 KL and needs site capacity review.")
    if _positive(record.quantity) and record.unit == "GAL":
        _add(issues, "WARNING", "SAP: GAL unit usually indicates a legacy interface or missing UOM conversion.")

    if record.lifnr.isnumeric() and len(record.lifnr) < 10:
        _add(issues, "INFO", "SAP: Numeric LIFNR is shorter than 10 digits and should be zero-padded before joins.")
    fuel_records = _tenant_records(FuelRecord, record)
    if record.unit == "MT" and _fuel_has_unit(context, fuel_records, record, "TO"):
        _add(issues, "WARNING", "SAP: MATNR uses both MT and TO units; normalize before aggregation.")
    if record.kostl and record.aufnr:
        _add(issues, "WARNING", "SAP: KOSTL and AUFNR are both populated; account assignment may be duplicated.")
    if record.loekz == "X":
        _add(issues, "INFO", "SAP: LOEKZ deletion flag is set; exclude from spend and emissions totals.")
    if record.bwart == "102" and not _fuel_has_receipt_101(context, fuel_records, record):
        _add(issues, "WARNING", "SAP: BWART 102 reversal has no matching BWART 101 receipt in the upload scope.")
    if _fuel_has_duplicate(context, fuel_records, record):
        _add(issues, "WARNING", "SAP: Duplicate EBELN + EBELP + BUDAT + MENGE + BWART detected.")

    if record.matkl == "FUEL" and record.unit not in SAP_FUEL_UNITS:
        _add(issues, "ERROR", "SAP: Fuel material has unsupported unit for emissions factor mapping.")
    if record.matkl == "FUEL" and not _known_fuel_material(record):
        _add(issues, "ERROR", "SAP: Fuel material does not map to a known fuel type.")
    if record.bwart == "101" and record.bstyp == "U":
        _add(issues, "INFO", "SAP: Internal stock transfer should be excluded from supplier Scope 3 calculations.")

    return issues


def _validate_electricity(record):
    issues = []
    electricity_records = _tenant_records(ElectricityRecord, record)

    _required(issues, record.account_no, "Electricity: ACCOUNT_NO is required.")
    _required(issues, record.meter_id, "Electricity: METER_ID is required.")
    if record.billing_start is None or record.billing_end is None:
        _add(issues, "ERROR", "Electricity: PERIOD_START and PERIOD_END are required.")
    if _blank(_raw(record, "CONSUMPTION")) and _blank(_raw(record, "Consumption (kWh)")):
        _add(issues, "ERROR", "Electricity: CONSUMPTION is required.")
    _required(issues, record.consumption_unit, "Electricity: CONSUMPTION_UNIT is required.")
    if _blank(record.tariff_code):
        _add(issues, "WARNING", "Electricity: TARIFF_CODE is missing.")
    if record.total_bill_inr is None:
        _add(issues, "WARNING", "Electricity: TOTAL_BILL_INR is missing.")

    if record.kwh <= 0 and record.read_type == "ACT":
        _add(issues, "ERROR", "Electricity: Actual read has zero or negative consumption.")
    if record.kwh <= 0 and record.read_type == "EST":
        _add(issues, "WARNING", "Electricity: Estimated read has zero or negative consumption.")
    if record.billing_days is not None and record.billing_days < 20:
        _add(issues, "WARNING", "Electricity: Billing period is shorter than 20 days.")
    if record.billing_days is not None and record.billing_days > 40:
        _add(issues, "WARNING", "Electricity: Billing period is longer than 40 days.")
    if _all_present(record.meter_read_start, record.meter_read_end) and record.meter_read_end < record.meter_read_start and record.read_type == "ACT":
        _add(issues, "WARNING", "Electricity: Meter read end is lower than start; possible register rollover.")
    if _all_present(record.meter_read_start, record.meter_read_end) and _unit(record.consumption_unit) == "KWH":
        delta = record.meter_read_end - record.meter_read_start
        if abs(delta - record.kwh) > Decimal("5"):
            _add(issues, "WARNING", "Electricity: Meter register delta differs from billed consumption by more than 5 kWh.")

    trailing = list(
        electricity_records.filter(meter_id=record.meter_id, id__lt=record.id)
        .exclude(kwh=0)
        .order_by("-id")
        .values_list("kwh", flat=True)[:3]
    )
    if len(trailing) == 3:
        average = sum(trailing) / Decimal("3")
        if average > 0 and record.kwh > average * Decimal("3"):
            _add(issues, "WARNING", "Electricity: Consumption exceeds 3x trailing 3-bill average.")
        if average > 0 and record.kwh < average * Decimal("0.30"):
            _add(issues, "WARNING", "Electricity: Consumption is below 30% of trailing 3-bill average.")

    if _unit(record.consumption_unit) == "MWH" and record.kwh < 1:
        _add(issues, "WARNING", "Electricity: MWh consumption below 1 may indicate kWh entered as MWh.")
    if _all_present(record.max_demand, record.contracted_demand_kva) and record.max_demand > record.contracted_demand_kva * Decimal("1.20"):
        _add(issues, "WARNING", "Electricity: MAX_DEMAND exceeds contracted demand by more than 20%.")
    tariff_text = f"{record.tariff_code} {record.tariff_category} {record.hv_lv}".upper()
    if (record.max_demand is None or record.max_demand <= 0) and ("HT" in tariff_text or "EHV" in tariff_text):
        _add(issues, "ERROR", "Electricity: HT/EHV tariff has zero or missing demand reading.")
    if record.power_factor is not None and record.power_factor < Decimal("0.70"):
        _add(issues, "WARNING", "Electricity: POWER_FACTOR is below 0.70.")
    if record.power_factor is not None and record.power_factor > Decimal("1.0"):
        _add(issues, "ERROR", "Electricity: POWER_FACTOR cannot be greater than 1.0.")
    if _all_present(record.total_bill_inr, record.supply_charge_inr, record.energy_charge_inr) and record.total_bill_inr < record.supply_charge_inr + record.energy_charge_inr:
        _add(issues, "ERROR", "Electricity: TOTAL_BILL_INR is less than supply plus energy charges.")

    if record.billing_start and record.billing_end and record.billing_end < record.billing_start:
        _add(issues, "ERROR", "Electricity: PERIOD_END is before PERIOD_START.")
    prior = electricity_records.filter(
        meter_id=record.meter_id,
        billing_end__lt=record.billing_start,
    ).exclude(id=record.id).order_by("-billing_end").first() if record.billing_start else None
    if prior and prior.billing_end + timedelta(days=1) != record.billing_start:
        _add(issues, "WARNING", "Electricity: Billing period is not continuous with prior meter bill.")
    if _all_present(record.peak_kwh, record.offpeak_kwh, record.shoulder_kwh) and _unit(record.consumption_unit) == "KWH":
        tou_total = record.peak_kwh + record.offpeak_kwh + record.shoulder_kwh
        if abs(tou_total - record.kwh) > Decimal("1"):
            _add(issues, "ERROR", "Electricity: TOU components do not sum to CONSUMPTION.")
    if record.peak_kwh is not None and "TOU" not in tariff_text and "TIME" not in tariff_text:
        _add(issues, "WARNING", "Electricity: PEAK_KWH is populated on a tariff that does not look time-of-use.")
    if record.read_type == "EST":
        previous_reads = list(
            electricity_records.filter(meter_id=record.meter_id, id__lt=record.id)
            .order_by("-id")
            .values_list("read_type", flat=True)[:2]
        )
        if previous_reads == ["EST", "EST"]:
            _add(issues, "WARNING", "Electricity: Three consecutive estimated reads for this meter.")
    if record.bill_date and record.billing_end and record.bill_date < record.billing_end:
        _add(issues, "ERROR", "Electricity: BILL_DATE is before PERIOD_END.")
    if record.due_date and record.bill_date and record.due_date < record.bill_date:
        _add(issues, "ERROR", "Electricity: DUE_DATE is before BILL_DATE.")
    if record.demand_unit and electricity_records.filter(account_no=record.account_no).exclude(demand_unit__in=["", record.demand_unit]).exclude(id=record.id).exists():
        _add(issues, "WARNING", "Electricity: Inconsistent demand units within the same account.")
    if record.consumption_unit and electricity_records.filter(account_no=record.account_no).exclude(consumption_unit__in=["", record.consumption_unit]).exclude(id=record.id).exists():
        _add(issues, "WARNING", "Electricity: Account mixes kWh and MWh consumption units.")
    if record.discom and record.discom.upper() not in KNOWN_DISCOMS:
        _add(issues, "WARNING", "Electricity: DISCOM is not in the grid emission factor lookup.")
    if record.total_bill_inr == 0 and record.kwh > 0:
        _add(issues, "WARNING", "Electricity: Consumption exists but TOTAL_BILL_INR is zero.")

    return issues


def _validate_travel(record):
    issues = []
    travel_records = _tenant_records(TravelRecord, record)
    today = timezone.localdate()
    expense_type = record.expense_type.lower()
    is_air = "air" in expense_type
    is_hotel = "hotel" in expense_type
    is_ground = "ground" in expense_type or any(word in expense_type for word in ("taxi", "uber", "train", "metro", "car"))
    distance_present = not _blank(_raw(record, "DISTANCE_KM"))

    _required(issues, record.report_id, "Travel: REPORT_ID is required.")
    _required(issues, record.expense_type, "Travel: EXPENSE_TYPE is required.")
    if record.transaction_date is None:
        _add(issues, "ERROR", "Travel: TRANSACTION_DATE is required.")
    _required(issues, record.employee_id, "Travel: EMPLOYEE_ID is required.")
    if record.amount is None:
        _add(issues, "ERROR", "Travel: AMOUNT is required.")
    if record.amount is not None and _blank(record.currency):
        _add(issues, "WARNING", "Travel: CURRENCY is missing while AMOUNT is populated.")

    if is_air:
        if _blank(record.origin_iata) or _blank(record.destination_iata):
            _add(issues, "ERROR", "Travel Air: ORIGIN_IATA and DESTINATION_IATA are required.")
        if _blank(record.cabin_class):
            _add(issues, "WARNING", "Travel Air: CABIN_CLASS is missing.")
    if is_hotel:
        if _blank(record.hotel_city):
            _add(issues, "WARNING", "Travel Hotel: HOTEL_CITY is missing.")
        if record.check_in_date is None or record.check_out_date is None:
            _add(issues, "WARNING", "Travel Hotel: CHECK_IN_DATE and CHECK_OUT_DATE are required to derive nights.")
    if is_ground and _blank(record.ground_transport_type):
        _add(issues, "WARNING", "Travel Ground: GROUND_TRANSPORT_TYPE is missing.")

    if is_air and distance_present and record.distance_km <= 0:
        _add(issues, "ERROR", "Travel Air: DISTANCE_KM must be positive when populated.")
    if is_air and distance_present and record.distance_km > 20000:
        _add(issues, "WARNING", "Travel Air: DISTANCE_KM exceeds the maximum possible great-circle distance.")
    if is_air and distance_present and 0 < record.distance_km < 50:
        _add(issues, "WARNING", "Travel Air: DISTANCE_KM below 50 km is unlikely for scheduled air travel.")
    if is_air and distance_present and 1 <= record.distance_km <= 785 and record.cabin_class == "Business":
        _add(issues, "WARNING", "Travel Air: Business class on a domestic/short-haul route requires policy review.")
    if is_air and record.amount is not None and record.amount < 500:
        _add(issues, "WARNING", "Travel Air: AMOUNT below INR 500 is likely a fee, credit, or itemisation error.")
    if is_air and record.amount is not None and record.amount > 1500000:
        _add(issues, "WARNING", "Travel Air: AMOUNT above INR 15 lakh requires review.")
    if is_hotel and record.check_in_date and record.check_out_date:
        nights = (record.check_out_date - record.check_in_date).days
        if nights <= 0:
            _add(issues, "ERROR", "Travel Hotel: Check-out must be after check-in.")
        if nights > 30:
            _add(issues, "WARNING", "Travel Hotel: Stay exceeds 30 nights.")
        if record.amount is not None and nights > 0 and record.amount / nights < 500:
            _add(issues, "WARNING", "Travel Hotel: Effective nightly rate is below INR 500.")
    if is_ground and distance_present and record.distance_km > 800 and any(word in record.ground_transport_type.lower() for word in ("taxi", "uber")):
        _add(issues, "WARNING", "Travel Ground: Taxi/Uber distance above 800 km is implausible.")
    if is_ground and record.amount is not None and record.amount < 10:
        _add(issues, "WARNING", "Travel Ground: AMOUNT below INR 10 is likely a surcharge or currency issue.")
    if record.amount is not None and record.amount < 0:
        _add(issues, "ERROR", "Travel: Negative AMOUNT is a credit/reversal and must not be treated as positive spend.")

    if is_air and record.origin_iata and record.destination_iata and record.origin_iata == record.destination_iata:
        _add(issues, "ERROR", "Travel Air: ORIGIN_IATA and DESTINATION_IATA cannot be the same.")
    for field_name, code in (("ORIGIN_IATA", record.origin_iata), ("DESTINATION_IATA", record.destination_iata)):
        if code and not re.fullmatch(r"[A-Z]{3}", code):
            _add(issues, "ERROR", f"Travel Air: {field_name} must be a valid 3-letter IATA code.")
    if is_air and not distance_present:
        _add(issues, "INFO", "Travel Air: DISTANCE_KM is missing and must be resolved from IATA route data.")
    if record.transaction_date and record.transaction_date > today:
        _add(issues, "ERROR", "Travel: TRANSACTION_DATE is in the future.")
    if record.transaction_date and record.transaction_date < today - timedelta(days=365) and record.approval_status == "Pending":
        _add(issues, "WARNING", "Travel: Expense has been pending approval for more than one year.")
    if record.employee_id and record.transaction_date and record.amount is not None and travel_records.filter(
        employee_id=record.employee_id,
        transaction_date=record.transaction_date,
        expense_type=record.expense_type,
        amount=record.amount,
    ).exclude(id=record.id).exists():
        _add(issues, "WARNING", "Travel: Possible duplicate employee/date/expense/amount row.")
    if is_hotel and record.transaction_date and record.check_in_date and record.check_out_date:
        if record.transaction_date < record.check_in_date - timedelta(days=7) or record.transaction_date > record.check_out_date + timedelta(days=7):
            _add(issues, "WARNING", "Travel Hotel: TRANSACTION_DATE is more than 7 days outside stay dates.")
    if record.reimbursable == "No" and record.amount is not None and record.amount > 5000:
        _add(issues, "INFO", "Travel: Large non-reimbursable expense may still require Scope 3 classification review.")
    if record.approval_status == "Rejected":
        _add(issues, "INFO", "Travel: Rejected expense should be excluded from spend and emissions totals.")
    if record.policy_compliant == "No" and record.approval_status == "Approved":
        _add(issues, "INFO", "Travel: Approved out-of-policy trip should be included but logged for policy analysis.")
    if is_air and distance_present and record.cabin_class in {"Business", "First"} and record.distance_km < 785:
        _add(issues, "WARNING", "Travel Air: Business/First class factor should not be applied to domestic distance band.")
    if record.estimated_emissions_kgco2e is not None and record.estimated_emissions_kgco2e > 10000:
        _add(issues, "WARNING", "Travel: Estimated emissions exceed 10 tCO2e for one row.")
    expected_factor = _expected_travel_factor(record, is_air, is_hotel, is_ground, distance_present)
    if expected_factor and record.emission_factor is not None:
        tolerance = expected_factor * Decimal("0.10")
        if abs(record.emission_factor - expected_factor) > tolerance:
            _add(issues, "WARNING", "Travel: Emission factor differs from configured current-year factor by more than 10%.")
    if is_ground and not distance_present and record.amount is not None and record.amount < 500:
        _add(issues, "INFO", "Travel Ground: Use spend-based fallback for small ground transport receipt without distance.")
    if is_air and record.origin_iata and record.destination_iata and not distance_present:
        _add(issues, "INFO", "Travel Air: Route is populated but distance must be resolved before emissions calculation.")

    return issues


def _add(issues, severity, message):
    issues.append((getattr(ValidationIssue.Severity, severity), message))


def _record_ids_by_type(records):
    record_ids = {}
    for record in records:
        record_ids.setdefault(record.RECORD_TYPE, []).append(record.id)
    return record_ids


def _fuel_validation_context(records):
    records = [record for record in records if record.id]
    if not records:
        return None

    tenant_ids = {record.datasource.tenant_id for record in records}
    if len(tenant_ids) != 1:
        return None

    rows = FuelRecord.objects.filter(datasource__tenant_id=tenant_ids.pop()).values_list(
        "id",
        "matnr",
        "unit",
        "ebeln",
        "ebelp",
        "bwart",
        "budat",
        "quantity",
    )
    units_by_matnr = {}
    receipt_101_keys = set()
    duplicate_ids_by_key = {}
    for record_id, matnr, unit, ebeln, ebelp, bwart, budat, quantity in rows:
        if matnr:
            units_by_matnr.setdefault(matnr, set()).add(unit)
        if bwart == "101":
            receipt_101_keys.add((ebeln, ebelp))
        duplicate_ids_by_key.setdefault((ebeln, ebelp, budat, quantity, bwart), set()).add(record_id)

    return {
        "units_by_matnr": units_by_matnr,
        "receipt_101_keys": receipt_101_keys,
        "duplicate_ids_by_key": duplicate_ids_by_key,
    }


def _fuel_has_unit(context, fuel_records, record, unit):
    if context is not None:
        return unit in context["units_by_matnr"].get(record.matnr, set())
    return fuel_records.filter(matnr=record.matnr, unit=unit).exclude(id=record.id).exists()


def _fuel_has_receipt_101(context, fuel_records, record):
    if context is not None:
        return (record.ebeln, record.ebelp) in context["receipt_101_keys"]
    return fuel_records.filter(ebeln=record.ebeln, ebelp=record.ebelp, bwart="101").exclude(id=record.id).exists()


def _fuel_has_duplicate(context, fuel_records, record):
    if context is not None:
        record_ids = context["duplicate_ids_by_key"].get(
            (record.ebeln, record.ebelp, record.budat, record.quantity, record.bwart),
            set(),
        )
        return bool(record_ids - {record.id})
    return fuel_records.filter(
        ebeln=record.ebeln,
        ebelp=record.ebelp,
        budat=record.budat,
        quantity=record.quantity,
        bwart=record.bwart,
    ).exclude(id=record.id).exists()


def _tenant_records(model, record):
    return model.objects.filter(datasource__tenant_id=record.datasource.tenant_id)


def _required(issues, value, message):
    if _blank(value):
        _add(issues, "ERROR", message)


def _blank(value):
    return value is None or str(value).strip() == ""


def _positive(value):
    return value is not None and value > 0


def _all_present(*values):
    return all(value is not None for value in values)


def _unit(value):
    return (value or "").strip().upper()


def _raw(record, key):
    target = _normalize_key(key)
    for raw_key, value in (record.source_payload or {}).items():
        if _normalize_key(raw_key) == target:
            return value
    return ""


def _normalize_key(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _known_fuel_material(record):
    text = f"{record.matnr} {record.txz01}".upper()
    return any(prefix in text for prefix in KNOWN_FUEL_PREFIXES)


def _expected_travel_factor(record, is_air, is_hotel, is_ground, distance_present):
    if is_air and distance_present:
        cabin = record.cabin_class.lower()
        if record.distance_km < 785:
            return Decimal("0.158")
        if record.distance_km < 3700:
            return Decimal("0.431") if "business" in cabin or "first" in cabin else Decimal("0.146")
        if "first" in cabin:
            return Decimal("0.966")
        if "business" in cabin:
            return Decimal("0.322")
        return Decimal("0.102")
    if is_hotel:
        return Decimal("20.500")
    if is_ground:
        mode = record.ground_transport_type.lower()
        if "train" in mode or "metro" in mode:
            return Decimal("0.041")
        if "taxi" in mode or "uber" in mode:
            return Decimal("0.149")
        if "car" in mode:
            return Decimal("0.170")
    return None
