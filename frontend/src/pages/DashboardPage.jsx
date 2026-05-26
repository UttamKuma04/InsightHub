import CloseIcon from "@mui/icons-material/Close";
import {
  Alert,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

const cards = [
  { key: "total_uploads", label: "Total Uploads" },
  { key: "total_fuel_records", label: "Fuel Records" },
  { key: "total_electricity_records", label: "Electricity Records" },
  { key: "total_travel_records", label: "Travel Records" },
  { key: "pending_reviews", label: "Pending Reviews" },
  { key: "approved_records", label: "Approved Records" },
  { key: "rejected_records", label: "Rejected Records" },
  { key: "validation_warnings", label: "Validation Warnings" },
  { key: "validation_errors", label: "Validation Errors" }
];

export default function DashboardPage() {
  const [activeMetric, setActiveMetric] = useState(null);

  const query = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const response = await api.get("/dashboard");
      return response.data;
    }
  });

  const drilldownQuery = useQuery({
    queryKey: ["dashboard-drilldown", activeMetric],
    enabled: Boolean(activeMetric),
    queryFn: async () => {
      const response = await api.get("/dashboard/drilldown", {
        params: { metric: activeMetric }
      });
      return response.data;
    }
  });

  return (
    <Box>
      <PageHeader title="Dashboard" subtitle="Tenant-level ingestion and review summary" />
      {query.isLoading && <LinearProgress sx={{ mb: 2 }} />}
      {query.isError && <Alert severity="error">Unable to load dashboard.</Alert>}
      <Grid container spacing={2}>
        {cards.map((card) => (
          <Grid item xs={12} sm={6} md={4} key={card.key}>
            <Card>
              <CardActionArea onClick={() => setActiveMetric(card.key)}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    {card.label}
                  </Typography>
                  <Typography variant="h4">{query.data?.[card.key] ?? 0}</Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog
        open={Boolean(activeMetric)}
        onClose={() => setActiveMetric(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ pr: 6 }}>
          {drilldownQuery.data?.title || "Details"}
          <IconButton
            aria-label="Close details"
            onClick={() => setActiveMetric(null)}
            sx={{ position: "absolute", right: 12, top: 10 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {drilldownQuery.isLoading && <LinearProgress sx={{ mb: 2 }} />}
          {drilldownQuery.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Unable to load details.
            </Alert>
          )}
          {drilldownQuery.data && <DrilldownTable data={drilldownQuery.data} />}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

function DrilldownTable({ data }) {
  const rows = data.rows || [];
  const columns = data.columns || [];

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column.key}>{column.label}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={`${row.record_type || row.source_type || "row"}-${row.record_id || row.id || index}`} hover>
              {columns.map((column) => (
                <TableCell key={column.key}>{formatCell(row[column.key])}</TableCell>
              ))}
            </TableRow>
          ))}
          {!rows.length && (
            <TableRow>
              <TableCell colSpan={columns.length || 1}>
                <Typography color="text.secondary" sx={{ py: 3, textAlign: "center" }}>
                  No matching data found.
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function formatCell(value) {
  if (!value) {
    return "-";
  }
  if (typeof value === "string" && value.includes("T")) {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString();
    }
  }
  return value;
}
