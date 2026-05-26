# Architecture and Source Decisions

Short justification for why InsightHub uses CSV-based source ingestion and why each source type keeps its current fields.

## Application Decisions

### CSV Uploads

- Chosen because SAP, utility portals, and travel tools commonly export CSV/Excel.
- Avoids tenant-specific APIs, OAuth setup, vendor onboarding, and custom connectors.
- Keeps the prototype usable by analysts without enterprise integration work.

### Modular Monolith

| Module | Responsibility |
| --- | --- |
| `core` | Tenants, users, permissions, demo data |
| `ingestion` | Upload jobs, CSV parsing, record APIs |
| `validation_service` | Validation rules and issues |
| `review` | Approve/reject workflow |
| `audit` | Immutable action history |
| `dashboard` | Metrics and drilldowns |


### Async Upload Processing

- Upload request saves the file and creates an `UploadJob`.
- Celery processes CSV rows in the background.
- Browser stays responsive and upload failures remain trackable.

### Redis

| Use | Decision |
| --- | --- |
| Celery broker | Queue upload processing jobs. |
| Django cache | Cache dashboard, audit, and list responses. |

### Storage

- Production files use Supabase S3-compatible storage.
- Local `media/` is only suitable for development.
- Shared object storage avoids file availability issues between web and worker processes.

### Separate Record Tables

- Fuel, electricity, and travel have different fields.
- Each source has different validation and review rules.
- Separate tables are clearer than one generic JSON table.

### Auth and Database

- JWT is used for stateless frontend/backend API auth.
- PostgreSQL is the target database.
- SQLite remains a local fallback.

## Source Decision 1: SAP Fuel Procurement

### Source Type

Accepted source: joined SAP procurement and material movement CSV.

| Table | Purpose |
| --- | --- |
| `EKKO` | PO header: vendor, currency, document type, dates |
| `EKPO` | PO item: material, quantity, price, plant |
| `MSEG` | Goods movement: receipt, reversal, return, posting date |

Why 3 tables:

- PO header shows who/what commercial document was raised.
- PO item shows material, unit, price, and receiving location.
- Material document shows what actually moved.
- ESG fuel activity needs movement evidence, not only PO intent.

### Key Joins

| Key | Meaning |
| --- | --- |
| `EBELN` | PO header key |
| `EBELN + EBELP` | Unique PO line |
| `MBLNR + MJAHR + ZEILE` | Unique material document line |

### `EKKO` Header Fields

| Column | SAP Field | Why Kept |
| --- | --- | --- |
| `EBELN` | `EKKO.EBELN` | PO number and join key |
| `BSART` | `EKKO.BSART` | PO document type |
| `BSTYP` | `EKKO.BSTYP` | External PO vs internal transfer category |
| `STATU` | `EKKO.STATU` | Open, blocked, or completed status |
| `AEDAT` | `EKKO.AEDAT` | Last changed date |
| `BEDAT` | `EKKO.BEDAT` | PO document date |
| `LIFNR` | `EKKO.LIFNR` | Vendor number; leading zeros matter |
| `VENDOR_NAME` | `LFA1.NAME1` | Readable vendor name |
| `EKORG` | `EKKO.EKORG` | Purchasing organization |
| `EKGRP` | `EKKO.EKGRP` | Buyer/purchasing group |
| `WAERS` | `EKKO.WAERS` | Currency |
| `WKURS` | `EKKO.WKURS` | Exchange rate |
| `INCO1` | `EKKO.INCO1` | Delivery responsibility terms |
| `ZTERMS` | `EKKO.ZTERMS` | Payment terms |

### `EKPO` Item Fields

| Column | SAP Field | Why Kept |
| --- | --- | --- |
| `EBELP` | `EKPO.EBELP` | PO line number |
| `MATNR` | `EKPO.MATNR` | Material/fuel code |
| `TXZ01` | `EKPO.TXZ01` | Material description |
| `MATKL` | `EKPO.MATKL` | Material group |
| `WERKS` | `EKPO.WERKS` | Receiving plant |
| `LGORT` | `EKPO.LGORT` | Storage location |
| `MENGE` | `EKPO.MENGE` | Ordered quantity |
| `MEINS` | `EKPO.MEINS` | Unit of measure |
| `NETPR` | `EKPO.NETPR` | Unit price |
| `NETWR` | `EKPO.NETWR` | Line value |
| `LOEKZ` | `EKPO.LOEKZ` | Deleted/cancelled line flag |

### `MSEG` Movement Fields

| Column | SAP Field | Why Kept |
| --- | --- | --- |
| `BWART` | `MSEG.BWART` | Movement type, e.g. receipt or reversal |
| `BUDAT` | `MSEG.BUDAT` | Posting date |
| `MBLNR` | `MSEG.MBLNR` | Material document number |
| `MJAHR` | `MSEG.MJAHR` | Material document year |
| `ZEILE` | `MSEG.ZEILE` | Material document line |
| `KOSTL` | `MSEG.KOSTL` | Cost center |
| `AUFNR` | `MSEG.AUFNR` | Internal order |

### Metadata

| Column | Why Kept |
| --- | --- |
| `DELET_FLAG` | Client-added deletion/status field; preserved for lineage |
| `SECTION_SOURCE` | Identifies extract batch/source |

### Main Data Issues

| Issue | Impact |
| --- | --- |
| Mixed date formats | Date parsing must be flexible |
| Vendor leading zeros | Joins can fail silently |
| Mixed units | Quantities need unit conversion |
| `BWART=102` reversals | Must not be counted as fresh receipts |
| `LOEKZ=X` | Deleted lines must be excluded |
| Both `KOSTL` and `AUFNR` filled | Account assignment needs review |

Decision: keep full SAP lineage because reviewers need PO, material, movement, unit, cost, and source context.

## Source Decision 2: Utility Electricity

### Source Type

Accepted source: utility portal CSV/Excel bill or account statement export.

### Alternatives

| Option | Decision | Reason |
| --- | --- | --- |
| PDF bill | Rejected | Needs OCR and layout-specific parsing |
| Utility API | Rejected | Access varies by DISCOM and account |
| Portal CSV/Excel | Accepted | Common, practical, and analyst-friendly |

### Identity Fields

| Column | Why Kept |
| --- | --- |
| `ACCOUNT_NO` | Utility account identifier |
| `METER_ID` | Meter-level tracking |
| `SITE_NAME` | Reviewer-friendly site name |
| `ADDRESS` | Location and duplicate checks |
| `CITY` | City-level reporting |
| `STATE` | State-level reporting |
| `DISCOM` | Utility provider and tariff context |

### Tariff Fields

| Column | Why Kept |
| --- | --- |
| `TARIFF_CATEGORY` | Broad tariff class |
| `TARIFF_CODE` | Utility-specific tariff |
| `SUPPLY_VOLTAGE` | Voltage-based tariff context |
| `HV_LV` | HT/LT classification |
| `CONTRACTED_DEMAND_KVA` | Sanctioned demand reference |

### Billing Period Fields

| Column | Why Kept |
| --- | --- |
| `PERIOD_START` | Actual bill start date |
| `PERIOD_END` | Actual bill end date |
| `BILLING_DAYS` | Normalized period comparison |
| `BILL_DATE` | Invoice date |
| `DUE_DATE` | Payment due date |

### Meter Reading Fields

| Column | Why Kept |
| --- | --- |
| `METER_READ_START` | Opening reading |
| `METER_READ_END` | Closing reading |
| `READ_TYPE` | Actual vs estimated read |

### Consumption Fields

| Column | Why Kept |
| --- | --- |
| `CONSUMPTION` | Main energy quantity |
| `CONSUMPTION_UNIT` | `kWh`/`MWh` normalization |
| `PEAK_KWH` | Peak usage |
| `OFFPEAK_KWH` | Off-peak usage |
| `SHOULDER_KWH` | Shoulder-period usage |

### Demand Fields

| Column | Why Kept |
| --- | --- |
| `MAX_DEMAND` | Peak demand in billing cycle |
| `DEMAND_UNIT` | `kW` vs `kVA` |
| `POWER_FACTOR` | Power quality and penalty checks |

### Charge Fields

| Column | Why Kept |
| --- | --- |
| `SUPPLY_CHARGE_INR` | Fixed supply charge |
| `ENERGY_CHARGE_INR` | Usage charge |
| `DEMAND_CHARGE_INR` | Demand charge |
| `PF_PENALTY_INR` | Power factor penalty |
| `REGULATORY_CHARGE_INR` | Surcharge/adjustment line items |
| `ELECTRICITY_DUTY_INR` | Statutory duty |
| `TOTAL_BILL_INR` | Bill reconciliation |
| `CURRENCY` | Currency context |
| `BILL_REFERENCE` | Invoice traceability |
| `PAYMENT_STATUS` | Finance review context |

### Main Data Issues

| Issue | Impact |
| --- | --- |
| Non-calendar billing cycles | Monthly reporting needs allocation |
| Estimated reads | Consumption may be corrected later |
| Multiple meters per site | Aggregation must preserve meter detail |
| Mixed units | `kWh` and `MWh` must be normalized |
| `kW` vs `kVA` demand | Demand values are not directly comparable |
| Tariff-dependent blanks | Blank charge fields may be valid |

Decision: keep billing, meter, tariff, demand, and charge details because electricity review needs more than one `kWh` value.

## Source Decision 3: Corporate Travel

### Source Type

Accepted source: SAP Concur-style analytics or expense processor CSV.

### Alternatives

| Option | Decision | Reason |
| --- | --- | --- |
| Concur API | Rejected | Requires tenant OAuth and IT setup |
| Manual employee export | Rejected | Not structured or scalable |
| Analytics/processor CSV | Accepted | Gives portfolio-level line data |

### Report Fields

| Column | Why Kept |
| --- | --- |
| `REPORT_ID` | Source report traceability |
| `EXPENSE_TYPE` | Drives air/hotel/ground logic |
| `TRANSACTION_DATE` | Reporting period |

### Employee Fields

| Column | Why Kept |
| --- | --- |
| `EMPLOYEE_ID` | Employee grouping |
| `EMPLOYEE_NAME` | Reviewer context |
| `DEPARTMENT` | Organization reporting |
| `COST_CENTER` | Finance ownership |
| `JOB_TITLE` | Policy review context |
| `HOME_CITY` | Route context |
| `TRIP_PURPOSE` | Business reason |
| `PAYMENT_METHOD` | Payment context |

### Flight Fields

| Column | Why Kept |
| --- | --- |
| `ORIGIN_IATA` | Route distance lookup |
| `DESTINATION_IATA` | Route distance lookup |
| `ORIGIN_CITY` | Reviewer context |
| `DESTINATION_CITY` | Reviewer context |
| `DISTANCE_KM` | Emissions calculation |
| `AIRLINE_CODE` | Carrier traceability |
| `AIRLINE_NAME` | Readable carrier name |
| `FLIGHT_NUMBER` | Booking traceability |
| `CABIN_CLASS` | Emission factor selection |

### Hotel Fields

| Column | Why Kept |
| --- | --- |
| `HOTEL_NAME` | Stay traceability |
| `HOTEL_CITY` | Regional emission factor |
| `CHECK_IN_DATE` | Start of stay |
| `CHECK_OUT_DATE` | Derive room nights |

### Ground Transport Fields

| Column | Why Kept |
| --- | --- |
| `GROUND_TRANSPORT_TYPE` | Taxi/train/car/bus classification |

### Spend Fields

| Column | Why Kept |
| --- | --- |
| `AMOUNT` | Spend and fallback estimates |
| `CURRENCY` | Currency normalization |
| `REIMBURSABLE` | Reimbursement context |

### Emissions Fields

| Column | Why Kept |
| --- | --- |
| `EMISSION_FACTOR_KGCO2E_PER_KM_OR_NIGHT` | Factor used |
| `ESTIMATED_EMISSIONS_KGCO2E` | Calculated/source emissions |

### Policy and Audit Fields

| Column | Why Kept |
| --- | --- |
| `POLICY_COMPLIANT` | Policy status |
| `POLICY_EXCEPTION_REASON` | Exception reason |
| `APPROVAL_STATUS` | Workflow status |
| `RECEIPT_ATTACHED` | Audit trigger |
| `NOTES` | Extra source context |

### Main Data Issues

| Issue | Impact |
| --- | --- |
| Missing flight distance | Needs IATA distance enrichment |
| Missing ground distance | Needs manual or spend-based estimate |
| Custom expense types | Requires mapping |
| Missing department/cost center | Depends on Concur setup |
| Missing receipts | Audit risk |
| Policy exceptions | Needs reviewer attention |

Decision: keep route, employee, spend, policy, receipt, and emissions context because Scope 3 travel review needs more than trip distance.

## Overall Source Strategy

| Source | Accepted Input | Why |
| --- | --- | --- |
| SAP fuel | SAP procurement + movement CSV | Keeps PO and movement lineage |
| Utility electricity | Portal bill/account CSV | Keeps meter, billing, demand, and charge detail |
| Corporate travel | Analytics/processor CSV | Keeps employee, route, policy, and emissions detail |

Final decision: ingest imperfect flat files, preserve source lineage, then surface issues through validation and review.
