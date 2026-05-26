# Sources and Research Notes

This prototype uses real-world-style CSV assumptions based on common enterprise export patterns rather than live vendor integrations.

## SAP Fuel Exports

Assumption: SAP fuel/procurement activity can be exported from purchasing and material movement tables such as EKKO, EKPO, and MSEG.

Accepted SAP export fields:

- `EBELN`, `EBELP` -> PO number and item
- `BEDAT`, `AEDAT`, `BUDAT` -> document, change, and posting dates
- `LIFNR`, `VENDOR_NAME` -> vendor lineage
- `MATNR`, `TXZ01`, `MATKL` -> material and fuel classification
- `WERKS` -> `plant_code`
- `MENGE` -> `quantity`
- `MEINS` -> `unit`
- `NETPR`, `NETWR`, `WAERS` -> commercial values
- `BWART`, `MBLNR` -> material movement lineage
- `KOSTL`, `AUFNR`, `LOEKZ` -> account assignment and deletion state

The ingestion service also accepts the original assignment headers: `date`, `plant_code`, `fuel_type`, `quantity`, and `unit`.

Real-world limitation: SAP landscapes vary by module, customization, units of measure, plant hierarchy, and posting process. A production connector would need field mapping, unit master data, duplicate detection, and reconciliation to source documents.

## Utility Electricity Exports

Assumption: utility or meter data can be exported by account, meter, billing period, consumption, demand, charge components, and payment status.

Accepted utility export fields:

- `ACCOUNT_NO`, `METER_ID`, `SITE_NAME`
- `PERIOD_START`, `PERIOD_END`, `BILLING_DAYS`
- `BILL_DATE`, `DUE_DATE`
- `METER_READ_START`, `METER_READ_END`, `READ_TYPE`
- `CONSUMPTION`, `CONSUMPTION_UNIT`
- `PEAK_KWH`, `OFFPEAK_KWH`, `SHOULDER_KWH`
- `MAX_DEMAND`, `DEMAND_UNIT`, `POWER_FACTOR`
- `SUPPLY_CHARGE_INR`, `ENERGY_CHARGE_INR`, `DEMAND_CHARGE_INR`, `TOTAL_BILL_INR`
- `DISCOM`, `TARIFF_CODE`, `CONTRACTED_DEMAND_KVA`

The ingestion service also accepts the original assignment headers: `meter_id`, `billing_start`, `billing_end`, and `kwh`.

Real-world limitation: utility data often includes tariffs, demand charges, estimated readings, multiple meters per site, time-of-use periods, renewable certificates, and invoice adjustments. The assignment only needs energy quantity validation.

## Travel Exports

Assumption: corporate travel systems can export Concur-style expense rows with employee, report, route, hotel, ground transport, policy, amount, and emissions fields.

Accepted travel export fields:

- `REPORT_ID`, `EXPENSE_TYPE`, `TRANSACTION_DATE`
- `EMPLOYEE_ID`, `EMPLOYEE_NAME`, `DEPARTMENT`, `COST_CENTER`
- `ORIGIN_IATA`, `DESTINATION_IATA`, `DISTANCE_KM`
- `CABIN_CLASS`, `AIRLINE_CODE`, `FLIGHT_NUMBER`
- `HOTEL_CITY`, `CHECK_IN_DATE`, `CHECK_OUT_DATE`
- `GROUND_TRANSPORT_TYPE`
- `AMOUNT`, `CURRENCY`, `REIMBURSABLE`
- `POLICY_COMPLIANT`, `APPROVAL_STATUS`
- `EMISSION_FACTOR_KGCO2E_PER_KM_OR_NIGHT`, `ESTIMATED_EMISSIONS_KGCO2E`

The ingestion service also accepts the original assignment headers `trip_type`, `origin`, `destination`, and `distance_km`.

Real-world limitation: travel emissions calculations usually need mode-specific factors, cabin class, round trips, passenger counts, hotel nights, rental cars, and source booking references. This prototype stores distance only because emission calculation is not required.

## Sample Data Assumptions

Sample files in `samples/` include valid rows and rows that intentionally trigger validation warnings/errors. This supports quick reviewer testing of:

- successful ingestion
- fuel unit normalization
- validation issue creation
- analyst approval/rejection
- audit logging
