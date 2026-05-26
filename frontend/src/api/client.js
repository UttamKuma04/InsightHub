import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  // Render free tier can take up to ~50s to cold-start; give it 60s.
  timeout: 60000
});

let refreshRequest = null;

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  const isRefreshRequest = config.url?.includes("/auth/refresh");
  if (token && !isRefreshRequest) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const refresh = localStorage.getItem("refresh");
    const isRefreshRequest = originalRequest?.url?.includes("/auth/refresh");

    // --- 401 → token refresh and retry ---
    if (error.response?.status === 401 && refresh && originalRequest && !originalRequest._retry && !isRefreshRequest) {
      originalRequest._retry = true;

      try {
        refreshRequest =
          refreshRequest ||
          api.post("/auth/refresh", { refresh }).finally(() => {
            refreshRequest = null;
          });

        const response = await refreshRequest;
        localStorage.setItem("access", response.data.access);
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        localStorage.removeItem("user");
        return Promise.reject(refreshError);
      }
    }

    if (error.response?.status === 401) {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("user");
    }

    // Tag errors that mean "the proxy/network gave up before the backend
    // responded" — the backend may have already committed the action.
    // Covers:
    //   - axios ECONNABORTED / Network Error  (client-side timeout)
    //   - 502 Bad Gateway  (Vercel/Render not yet ready)
    //   - 503 Service Unavailable
    //   - 504 Gateway Timeout  (Vercel proxy timed out waiting for Render)
    const isGatewayTimeout =
      !error.response && (error.code === "ECONNABORTED" || error.message === "Network Error");
    const isGatewayError = [502, 503, 504].includes(error.response?.status);
    if (isGatewayTimeout || isGatewayError) {
      error._isTimeout = true;
    }

    return Promise.reject(error);
  }
);
