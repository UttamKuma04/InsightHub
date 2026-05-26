import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  Typography
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

const pendingJobsStorageKey = "pendingUploadJobs";

const uploadTargets = [
  { key: "sap", label: "SAP Fuel CSV", endpoint: "/upload/sap" },
  { key: "utility", label: "Utility CSV", endpoint: "/upload/utility" },
  { key: "travel", label: "Travel CSV", endpoint: "/upload/travel" }
];

function getPendingJobs() {
  try {
    return JSON.parse(localStorage.getItem(pendingJobsStorageKey) || "[]");
  } catch {
    return [];
  }
}

function savePendingJobs(jobs) {
  localStorage.setItem(pendingJobsStorageKey, JSON.stringify(jobs));
}

function uploadErrorMessage(error, fallback) {
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

export default function UploadPage() {
  const queryClient = useQueryClient();
  const [files, setFiles] = useState({});
  const [uploading, setUploading] = useState({});
  const [retryError, setRetryError] = useState("");
  const [messages, setMessages] = useState(() =>
    getPendingJobs().reduce((current, job) => {
      current[job.targetKey] = { severity: "info", text: "Uploading in process." };
      return current;
    }, {})
  );

  const mutation = useMutation({
    mutationFn: async ({ endpoint, file, targetKey }) => {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return { ...response.data, targetKey };
    },
    onMutate: ({ targetKey }) => {
      setUploading((current) => ({ ...current, [targetKey]: true }));
      setMessages((current) => ({ ...current, [targetKey]: { severity: "info", text: "Uploading in process." } }));
    },
    onSuccess: (data) => {
      const pendingJobs = getPendingJobs();
      savePendingJobs([
        ...pendingJobs.filter((job) => job.uploadJobId !== data.upload_job_id),
        { uploadJobId: data.upload_job_id, targetKey: data.targetKey }
      ]);
      setMessages((current) => ({
        ...current,
        [data.targetKey]: { severity: "success", text: "Uploading in process." }
      }));
    },
    onError: (error, variables) => {
      setMessages((current) => ({
        ...current,
        [variables.targetKey]: {
          severity: "error",
          text: uploadErrorMessage(error, "Upload failed. Check backend logs.")
        }
      }));
    },
    onSettled: (_, __, variables) => {
      setUploading((current) => ({ ...current, [variables.targetKey]: false }));
    }
  });
  const jobsQuery = useQuery({
    queryKey: ["upload-jobs"],
    queryFn: async () => {
      const response = await api.get("/upload/jobs");
      return response.data;
    },
    refetchInterval: 3000
  });

  const retryMutation = useMutation({
    mutationFn: async (jobId) => {
      const response = await api.post(`/upload/jobs/${jobId}/retry`);
      return response.data;
    },
    onMutate: () => {
      setRetryError("");
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["upload-jobs"] }),
    onError: (error) => {
      setRetryError(uploadErrorMessage(error, "Retry failed. Check backend logs."));
    }
  });

  useEffect(() => {
    async function checkPendingJobs() {
      const pendingJobs = getPendingJobs();
      if (!pendingJobs.length) {
        return;
      }

      const remainingJobs = [];
      for (const job of pendingJobs) {
        try {
          const response = await api.get(`/upload/jobs/${job.uploadJobId}`);
          if (["QUEUED", "PROCESSING"].includes(response.data.status)) {
            remainingJobs.push(job);
            setMessages((current) => ({
              ...current,
              [job.targetKey]: { severity: "info", text: "Uploading in process." }
            }));
          } else if (response.data.status === "COMPLETED") {
            setMessages((current) => ({
              ...current,
              [job.targetKey]: { severity: "success", text: "Upload completed, records available." }
            }));
            queryClient.invalidateQueries({ queryKey: ["/dashboard"] });
            queryClient.invalidateQueries({ queryKey: ["/fuel"] });
            queryClient.invalidateQueries({ queryKey: ["/electricity"] });
            queryClient.invalidateQueries({ queryKey: ["/travel"] });
            queryClient.invalidateQueries({ queryKey: ["upload-jobs"] });
          } else {
            setMessages((current) => ({
              ...current,
              [job.targetKey]: { severity: "error", text: response.data.error_message || "Upload failed." }
            }));
          }
        } catch {
          remainingJobs.push(job);
        }
      }
      savePendingJobs(remainingJobs);
    }

    checkPendingJobs();
    const interval = window.setInterval(checkPendingJobs, 3000);

    return () => window.clearInterval(interval);
  }, [queryClient]);

  return (
    <Box>
      <PageHeader title="Upload" subtitle="CSV ingestion by source system" />
      <Grid container spacing={2}>
        {uploadTargets.map((target) => (
          <Grid item xs={12} md={4} key={target.key}>
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  <Typography variant="h6">{target.label}</Typography>
                  <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                    Select CSV
                    <input
                      hidden
                      type="file"
                      accept=".csv,text/csv"
                      onChange={(event) =>
                        setFiles((current) => ({
                          ...current,
                          [target.key]: event.target.files?.[0]
                        }))
                      }
                    />
                  </Button>
                  <Typography variant="body2" color="text.secondary" noWrap>
                    {files[target.key]?.name || "No file selected"}
                  </Typography>
                  <Button
                    variant="contained"
                    disabled={!files[target.key] || uploading[target.key]}
                    onClick={() =>
                      mutation.mutate({
                        endpoint: target.endpoint,
                        file: files[target.key],
                        targetKey: target.key
                      })
                    }
                  >
                    {uploading[target.key] ? "Uploading" : "Upload"}
                  </Button>
                  {messages[target.key] && (
                    <Alert severity={messages[target.key].severity}>{messages[target.key].text}</Alert>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {retryError && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {retryError}
        </Alert>
      )}
      <TableContainer component={Card} sx={{ mt: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>File</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Records</TableCell>
              <TableCell>Error</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(jobsQuery.data || []).map((job) => (
              <TableRow key={job.upload_job_id}>
                <TableCell>{job.filename}</TableCell>
                <TableCell>{job.source_type}</TableCell>
                <TableCell>{job.status}</TableCell>
                <TableCell>{job.total_records}</TableCell>
                <TableCell>{job.error_message || "-"}</TableCell>
                <TableCell align="right">
                  {job.status === "FAILED" && (
                    <Button
                      size="small"
                      disabled={retryMutation.isPending && retryMutation.variables === job.upload_job_id}
                      onClick={() => retryMutation.mutate(job.upload_job_id)}
                    >
                      {retryMutation.isPending && retryMutation.variables === job.upload_job_id ? "Retrying" : "Retry"}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {!jobsQuery.isLoading && !jobsQuery.data?.length && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
                    No upload jobs yet.
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
