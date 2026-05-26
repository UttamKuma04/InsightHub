import { Box, Typography } from "@mui/material";

export default function PageHeader({ title, subtitle }) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h4" sx={{ mb: 0.5 }}>
        {title}
      </Typography>
      {subtitle && (
        <Typography color="text.secondary" variant="body1">
          {subtitle}
        </Typography>
      )}
    </Box>
  );
}

