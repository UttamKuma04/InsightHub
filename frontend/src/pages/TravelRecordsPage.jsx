import RecordTable from "../components/RecordTable.jsx";

export default function TravelRecordsPage() {
  return (
    <RecordTable
      title="Travel Records"
      endpoint="/travel"
      recordType="TRAVEL"
      columns={[
        { key: "report_id", label: "Report" },
        { key: "expense_type", label: "Expense" },
        { key: "transaction_date", label: "Date" },
        { key: "employee_id", label: "Employee" },
        { key: "origin_iata", label: "Origin" },
        { key: "destination_iata", label: "Destination" },
        { key: "distance_km", label: "Distance km" },
        { key: "cabin_class", label: "Cabin" },
        { key: "hotel_city", label: "Hotel City" },
        { key: "ground_transport_type", label: "Ground Mode" },
        { key: "amount", label: "Amount" },
        { key: "approval_status", label: "Approval" }
      ]}
    />
  );
}
