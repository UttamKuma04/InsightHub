import RecordTable from "../components/RecordTable.jsx";

export default function ElectricityRecordsPage() {
  return (
    <RecordTable
      title="Electricity Records"
      endpoint="/electricity"
      recordType="ELECTRICITY"
      columns={[
        { key: "account_no", label: "Account" },
        { key: "meter_id", label: "Meter" },
        { key: "site_name", label: "Site" },
        { key: "discom", label: "DISCOM" },
        { key: "tariff_code", label: "Tariff" },
        { key: "billing_start", label: "Start" },
        { key: "billing_end", label: "End" },
        { key: "billing_days", label: "Days" },
        { key: "read_type", label: "Read" },
        { key: "kwh", label: "Consumption" },
        { key: "consumption_unit", label: "Unit" },
        { key: "total_bill_inr", label: "Bill" }
      ]}
    />
  );
}
