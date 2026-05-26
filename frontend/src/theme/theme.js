import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1f5f8b"
    },
    secondary: {
      main: "#2f7d5b"
    },
    warning: {
      main: "#b56b16"
    },
    error: {
      main: "#b42318"
    },
    background: {
      default: "#f7f9fb",
      paper: "#ffffff"
    }
  },
  shape: {
    borderRadius: 8
  },
  typography: {
    fontFamily: [
      "Inter",
      "Segoe UI",
      "Roboto",
      "Arial",
      "sans-serif"
    ].join(","),
    h4: {
      fontWeight: 700
    },
    h6: {
      fontWeight: 700
    }
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: "1px solid #dbe3ea",
          boxShadow: "none"
        }
      }
    }
  }
});

