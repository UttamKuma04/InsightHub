import LockIcon from "@mui/icons-material/Lock";
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  Stack,
  TextField,
  Typography
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { login } from "../api/auth.js";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("analyst@insighthub.local");
  const [password, setPassword] = useState("analyst123");

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: () => navigate("/", { replace: true })
  });

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        bgcolor: "background.default",
        px: 2
      }}
    >
      <Container maxWidth="xs">
        <Paper sx={{ p: 4, border: "1px solid #dbe3ea", boxShadow: "none" }}>
          <Stack spacing={2.5}>
            <Box>
              <Stack direction="row" alignItems="center" spacing={1.25} sx={{ mb: 1 }}>
                <LockIcon color="primary" />
                <Typography variant="h5" fontWeight={700}>
                  InsightHub
                </Typography>
              </Stack>
              <Typography color="text.secondary">Analyst review workspace</Typography>
            </Box>
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
            />
            {mutation.isError && (
              <Alert severity="error">Login failed. Check the seeded demo credentials.</Alert>
            )}
            <Button
              variant="contained"
              size="large"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
            >
              Log in
            </Button>
          </Stack>
        </Paper>
      </Container>
    </Box>
  );
}
