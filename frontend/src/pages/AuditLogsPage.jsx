import {
  Alert,
  Box,
  Chip,
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

import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function AuditLogsPage() {
  const query = useQuery({
    queryKey: ["audit"],
    queryFn: async () => {
      const response = await api.get("/audit");
      return response.data;
    }
  });

  return (
    <Box>
      <PageHeader title="Audit Logs" />
      {query.isLoading && <LinearProgress sx={{ mb: 2 }} />}
      {query.isError && <Alert severity="error">Unable to load audit logs.</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Action</TableCell>
              <TableCell>Record</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Timestamp</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(query.data || []).map((log) => (
              <TableRow key={log.id} hover>
                <TableCell>
                  <Chip size="small" label={log.action} />
                </TableCell>
                <TableCell>
                  {log.record_type} #{log.record_id}
                </TableCell>
                <TableCell>{log.user}</TableCell>
                <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {Object.keys(log.details || {}).length ? JSON.stringify(log.details) : "-"}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
            {!query.isLoading && !query.data?.length && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary" sx={{ py: 3, textAlign: "center" }}>
                    No audit entries found.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
