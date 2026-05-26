# Data Model and Workflow

Simple reference for the main tables, relationships, and record lifecycle.

## Core Model

| Model | Purpose |
| --- | --- |
| `Tenant` | Company/workspace boundary |
| `User` | Tenant user with `ADMIN` or `ANALYST` role |
| `DataSource` | One uploaded CSV source file |
| `UploadJob` | Async upload processing status |
| `FuelRecord` | SAP fuel/procurement row |
| `ElectricityRecord` | Utility bill/meter row |
| `TravelRecord` | Corporate travel expense row |
| `ValidationIssue` | Validation message for one record |
| `AuditLog` | Immutable user/system action history |

## Database Architecture

![InsightHub database architecture](images/database_architecture.png)

## Tenant Isolation

- Every user belongs to one `Tenant`.
- Every `DataSource` belongs to one `Tenant`.
- Records are scoped through `record.datasource.tenant`.
- API queries filter by `request.user.tenant`.

Decision: shared database with tenant-scoped rows.

## Data Source Tracking

Each upload creates:

| Field | Purpose |
| --- | --- |
| `tenant` | Owns the uploaded data |
| `source_type` | `SAP`, `UTILITY`, or `TRAVEL` |
| `filename` | Original source filename |
| `uploaded_by` | User who uploaded the file |
| `uploaded_at` | Upload timestamp |

Each source record stores:

- normalized typed fields
- `source_payload` JSON copy of the original CSV row
- link back to `DataSource`

Why: typed fields support filtering/validation; `source_payload` preserves raw lineage.

## Upload Job

| Status | Meaning |
| --- | --- |
| `QUEUED` | File accepted |
| `PROCESSING` | Worker is reading rows |
| `COMPLETED` | Records created |
| `FAILED` | Upload failed with `error_message` |

Tracked fields:

- `total_records`
- `created_at`
- `started_at`
- `finished_at`

## Record Tables

### Shared Record Fields

| Field | Purpose |
| --- | --- |
| `datasource` | Source file lineage |
| `source_payload` | Original CSV row |
| `status` | `PENDING`, `APPROVED`, or `REJECTED` |
| `locked` | Prevents review changes after approval |

### `FuelRecord`

Main field groups:

| Group | Fields |
| --- | --- |
| PO identity | `ebeln`, `ebelp` |
| Header | `bsart`, `bstyp`, `statu`, `aedat`, `bedat` |
| Vendor/org | `lifnr`, `vendor_name`, `ekorg`, `ekgrp` |
| Material | `matnr`, `txz01`, `matkl` |
| Location | `werks`, `lgort`, `plant_code` |
| Quantity | `quantity`, `unit`, `normalized_quantity`, `fuel_type` |
| Commercial | `waers`, `wkurs`, `netpr`, `netwr`, `inco1`, `zterms` |
| Movement | `bwart`, `budat`, `mblnr`, `mjahr`, `zeile` |
| Account assignment | `kostl`, `aufnr` |
| Flags/source | `loekz`, `section_source` |

### `ElectricityRecord`

Main field groups:

| Group | Fields |
| --- | --- |
| Identity | `account_no`, `meter_id`, `site_name`, `address`, `city`, `state`, `discom` |
| Tariff | `tariff_category`, `tariff_code`, `supply_voltage`, `hv_lv`, `contracted_demand_kva` |
| Billing | `billing_start`, `billing_end`, `billing_days`, `bill_date`, `due_date` |
| Readings | `meter_read_start`, `meter_read_end`, `read_type` |
| Consumption | `kwh`, `consumption_unit`, `peak_kwh`, `offpeak_kwh`, `shoulder_kwh` |
| Demand | `max_demand`, `demand_unit`, `power_factor` |
| Charges | `supply_charge_inr`, `energy_charge_inr`, `demand_charge_inr`, `pf_penalty_inr`, `regulatory_charge_inr`, `electricity_duty_inr`, `total_bill_inr` |
| Finance | `currency`, `bill_reference`, `payment_status` |

### `TravelRecord`

Main field groups:

| Group | Fields |
| --- | --- |
| Report | `report_id`, `expense_type`, `transaction_date` |
| Employee | `employee_id`, `employee_name`, `department`, `cost_center`, `job_title`, `home_city` |
| Trip context | `trip_purpose`, `payment_method`, `trip_type`, `origin`, `destination` |
| Flight | `origin_iata`, `destination_iata`, `origin_city`, `destination_city`, `distance_km`, `airline_code`, `airline_name`, `flight_number`, `cabin_class` |
| Hotel | `hotel_name`, `hotel_city`, `check_in_date`, `check_out_date` |
| Ground | `ground_transport_type` |
| Spend | `amount`, `currency`, `reimbursable` |
| Policy | `policy_compliant`, `policy_exception_reason`, `approval_status`, `receipt_attached` |
| Emissions | `emission_factor`, `estimated_emissions_kgco2e` |
| Notes | `notes` |

## Processing Flow

```text
CSV upload
  -> UploadJob created
  -> DataSource created
  -> CSV rows normalized
  -> Fuel/Electricity/Travel records created
  -> RecordCreated signal emitted
  -> ValidationIssue rows created
  -> AuditLog CREATE row created
  -> Analyst approves or rejects
  -> AuditLog APPROVE/REJECT row created
```

## Validation Model

`ValidationIssue` fields:

| Field | Purpose |
| --- | --- |
| `record_type` | `FUEL`, `ELECTRICITY`, or `TRAVEL` |
| `record_id` | ID of the source-specific record |
| `severity` | `INFO`, `WARNING`, or `ERROR` |
| `message` | Human-readable issue |
| `created_at` | Issue timestamp |

Why no foreign key:

- fuel, electricity, and travel records live in separate tables
- `record_type + record_id` keeps validation generic

## Main Validation Areas

| Source | Checks |
| --- | --- |
| Fuel | required SAP keys, units, movement types, deletion flag, duplicate PO lines, cost assignment, emissions unit mapping |
| Electricity | required account/meter fields, billing period, consumption, units, meter deltas, demand, power factor, bill totals, TOU sums |
| Travel | required report/employee fields, route fields, distance bounds, hotel dates, ground mode, duplicate expenses, approval state, emissions factors |

## Review Workflow

Default state:

- `status = PENDING`
- `locked = false`

Approve:

- sets `status = APPROVED`
- sets `locked = true`
- creates audit entry

Reject:

- sets `status = REJECTED`
- keeps `locked = false`
- creates audit entry

Concurrency:

- review service uses `select_for_update()`
- prevents two reviewers from changing the same record at the same time

## Audit Trail

`AuditLog` actions:

| Action | Meaning |
| --- | --- |
| `CREATE` | Record created from upload |
| `EDIT` | Record edited |
| `APPROVE` | Record approved |
| `REJECT` | Record rejected |
| `DELETE` | Record deleted |

Audit fields:

- `action`
- `record_type`
- `record_id`
- `user`
- `timestamp`
- `details`

## Locking Rule

- Approved records are locked.
- Locked records cannot be approved/rejected again.
- This protects reviewed ESG data from normal analyst changes.
