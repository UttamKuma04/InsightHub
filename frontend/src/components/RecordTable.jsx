import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client.js";
import PageHeader from "./PageHeader.jsx";

const severityColors = {
  ERROR: "error",
  WARNING: "warning",
  INFO: "info"
};

function errorMessage(error, fallback) {
  const data = error.response?.data;
  if (data?.detail) {
    return data.detail;
  }
  if (typeof data === "string") {
    return data.trim().startsWith("<") ? fallback : data;
  }
  if (data) {
    return JSON.stringify(data);
  }
  return error.message || fallback;
}

export default function RecordTable({ title, endpoint, recordType, columns }) {
  const queryClient = useQueryClient();
  const [editingRow, setEditingRow] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const query = useQuery({
    queryKey: [endpoint, page, rowsPerPage, search, statusFilter, severityFilter],
    queryFn: async () => {
      const response = await api.get(endpoint, {
        params: {
          page: page + 1,
          page_size: rowsPerPage,
          search: search || undefined,
          status: statusFilter || undefined,
          severity: severityFilter || undefined
        }
      });
      return response.data;
    }
  });

  const [reviewingId, setReviewingId] = useState(null);

  const reviewMutation = useMutation({
    mutationFn: async ({ action, id }) => {
      setReviewingId(id);
      return api.post(`/review/${action}`, { record_type: recordType, record_id: id });
    },
    onSuccess: () => {
      setReviewingId(null);
      queryClient.invalidateQueries({ queryKey: [endpoint], exact: false });
    },
    onError: (error) => {
      setReviewingId(null);
      // Always refresh the table — if the backend committed before the proxy
      // timed out the refreshed data will show the correct status.
      queryClient.invalidateQueries({ queryKey: [endpoint], exact: false });
      // For gateway/timeout errors (502, 503, 504, network) the backend already
      // committed the action. Reset the mutation asynchronously so that React Query
      // does not overwrite the reset state during this error dispatch cycle.
      if (error._isTimeout) {
        setTimeout(() => {
          reviewMutation.reset();
        }, 0);
      }
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => api.delete(`${endpoint}/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [endpoint], exact: false })
  });

  const editMutation = useMutation({
    mutationFn: async ({ id, values }) => api.patch(`${endpoint}/${id}`, values),
    onSuccess: () => {
      setEditingRow(null);
      queryClient.invalidateQueries({ queryKey: [endpoint], exact: false });
    }
  });

  const editableColumns = useMemo(
    () => columns.filter((column) => column.editable !== false),
    [columns]
  );
  const visibleRows = query.data?.results || [];
  const totalRows = query.data?.count || 0;

  useEffect(() => {
    setPage(0);
  }, [endpoint, search, statusFilter, severityFilter]);

  const exportCsv = async () => {
    const response = await api.get(endpoint, {
      params: {
        export: "csv",
        search: search || undefined,
        status: statusFilter || undefined,
        severity: severityFilter || undefined
      },
      responseType: "blob"
    });
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${recordType.toLowerCase()}-records.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <PageHeader title={title} />
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ mb: 2 }}>
        <TextField
          label="Search"
          size="small"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <TextField
          label="Status"
          select
          size="small"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="PENDING">Pending</MenuItem>
          <MenuItem value="APPROVED">Approved</MenuItem>
          <MenuItem value="REJECTED">Rejected</MenuItem>
        </TextField>
        <TextField
          label="Issue"
          select
          size="small"
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value)}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="ERROR">Error</MenuItem>
          <MenuItem value="WARNING">Warning</MenuItem>
          <MenuItem value="INFO">Info</MenuItem>
        </TextField>
        <Button variant="outlined" onClick={exportCsv}>
          Export CSV
        </Button>
      </Stack>
      {query.isLoading && <LinearProgress sx={{ mb: 2 }} />}
      {query.isError && <Alert severity="error">Unable to load records.</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              {columns.map((column) => (
                <TableCell key={column.key}>{column.label}</TableCell>
              ))}
              <TableCell>Status</TableCell>
              <TableCell>Issues</TableCell>
              <TableCell align="right">Review</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRows.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.id}</TableCell>
                {columns.map((column) => (
                  <TableCell key={column.key}>{column.render ? column.render(row) : row[column.key]}</TableCell>
                ))}
                <TableCell>
                  <Chip
                    size="small"
                    label={row.status}
                    color={row.status === "APPROVED" ? "success" : row.status === "REJECTED" ? "error" : "default"}
                  />
                </TableCell>
                <TableCell sx={{ minWidth: 220 }}>
                  <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                    {row.issues?.length ? (
                      row.issues.map((issue) => (
                        <Tooltip title={issue.message} key={issue.id}>
                          <Chip
                            size="small"
                            label={issue.severity}
                            color={severityColors[issue.severity] || "default"}
                            variant="outlined"
                          />
                        </Tooltip>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        None
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button
                      size="small"
                      variant="contained"
                      color="secondary"
                      startIcon={<CheckCircleIcon />}
                      disabled={row.locked || reviewingId === row.id}
                      onClick={() => {
                        reviewMutation.reset();
                        reviewMutation.mutate({ action: "approve", id: row.id });
                      }}
                    >
                      {reviewingId === row.id ? "Approving…" : "Approve"}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      startIcon={<CancelIcon />}
                      disabled={row.locked || reviewingId === row.id}
                      onClick={() => {
                        reviewMutation.reset();
                        reviewMutation.mutate({ action: "reject", id: row.id });
                      }}
                    >
                      {reviewingId === row.id ? "Rejecting…" : "Reject"}
                    </Button>
                    <RowActions
                      row={row}
                      disabled={deleteMutation.isPending || editMutation.isPending || row.locked}
                      onEdit={() => setEditingRow(row)}
                      onDelete={() => deleteMutation.mutate(row.id)}
                    />
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!query.isLoading && !visibleRows.length && (
              <TableRow>
                <TableCell colSpan={columns.length + 4}>
                  <Typography color="text.secondary" sx={{ py: 3, textAlign: "center" }}>
                    No records found.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={totalRows}
        page={page}
        rowsPerPage={rowsPerPage}
        rowsPerPageOptions={[25, 50, 100]}
        onPageChange={(_, nextPage) => setPage(nextPage)}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
      />
      {reviewMutation.isError && !reviewMutation.error?._isTimeout && (
        <Alert severity="warning" sx={{ mt: 2 }} onClose={() => reviewMutation.reset()}>
          {errorMessage(reviewMutation.error, "Review action failed.")}
          {" The action may have still been saved — please refresh to confirm the current status."}
        </Alert>
      )}
      {deleteMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage(deleteMutation.error, "Delete failed.")}
        </Alert>
      )}
      {editMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage(editMutation.error, "Edit failed.")}
        </Alert>
      )}
      <EditRecordDialog
        columns={editableColumns}
        open={Boolean(editingRow)}
        row={editingRow}
        saving={editMutation.isPending}
        onClose={() => setEditingRow(null)}
        onSave={(values) => editMutation.mutate({ id: editingRow.id, values })}
      />
    </Box>
  );
}

function RowActions({ row, disabled, onEdit, onDelete }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleEdit = () => {
    setAnchorEl(null);
    onEdit();
  };

  const handleDelete = () => {
    setAnchorEl(null);
    if (window.confirm(`Delete ${row.id}?`)) {
      onDelete();
    }
  };

  return (
    <>
      <IconButton
        size="small"
        aria-label={`Open actions for row ${row.id}`}
        onClick={(event) => setAnchorEl(event.currentTarget)}
      >
        <MoreVertIcon fontSize="small" />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <MenuItem onClick={handleEdit} disabled={disabled}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete} disabled={disabled}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}

function EditRecordDialog({ columns, open, row, saving, onClose, onSave }) {
  const [values, setValues] = useState({});

  useEffect(() => {
    if (row) {
      setValues(buildInitialValues(columns, row));
    }
  }, [columns, row]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave(values);
  };

  return (
    <Dialog open={open} onClose={saving ? undefined : onClose} fullWidth maxWidth="sm">
      <Box component="form" onSubmit={handleSubmit}>
        <DialogTitle>Edit record {row?.id}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {columns.map((column) => (
              <TextField
                key={column.key}
                label={column.label}
                type={fieldType(column.key)}
                value={values[column.key] ?? ""}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    [column.key]: event.target.value
                  }))
                }
                fullWidth
                size="small"
                inputProps={fieldInputProps(column.key)}
              />
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={saving}>
            Save
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}

function buildInitialValues(columns, row) {
  return columns.reduce((values, column) => {
    values[column.key] = row?.[column.key] ?? "";
    return values;
  }, {});
}

function fieldType(key) {
  if (key.includes("date") || key.includes("billing_")) {
    return "date";
  }
  if (["quantity", "kwh", "distance_km"].includes(key)) {
    return "number";
  }
  return "text";
}

function fieldInputProps(key) {
  if (["quantity", "kwh", "distance_km"].includes(key)) {
    return { step: "0.001" };
  }
  return undefined;
}
