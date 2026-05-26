import RecordTable from "../components/RecordTable.jsx";

export default function FuelRecordsPage() {
  return (
    <RecordTable
      title="Fuel Records"
      endpoint="/fuel"
      recordType="FUEL"
      columns={[
        { key: "ebeln", label: "PO" },
        { key: "ebelp", label: "Item" },
        { key: "bedat", label: "Doc Date" },
        { key: "matnr", label: "Material" },
        { key: "txz01", label: "Description" },
        { key: "matkl", label: "Group" },
        { key: "werks", label: "Plant" },
        { key: "quantity", label: "Qty" },
        { key: "unit", label: "UOM" },
        { key: "netwr", label: "Net Value" },
        { key: "bwart", label: "Movement" }
      ]}
    />
  );
}
