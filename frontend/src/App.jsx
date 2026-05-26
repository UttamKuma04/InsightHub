import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import { isAuthenticated } from "./api/auth.js";
import AuditLogsPage from "./pages/AuditLogsPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import ElectricityRecordsPage from "./pages/ElectricityRecordsPage.jsx";
import FuelRecordsPage from "./pages/FuelRecordsPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import TravelRecordsPage from "./pages/TravelRecordsPage.jsx";
import UploadPage from "./pages/UploadPage.jsx";

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/fuel" element={<FuelRecordsPage />} />
          <Route path="/electricity" element={<ElectricityRecordsPage />} />
          <Route path="/travel" element={<TravelRecordsPage />} />
          <Route path="/audit" element={<AuditLogsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

