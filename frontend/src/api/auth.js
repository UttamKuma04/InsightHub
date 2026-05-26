import { api } from "./client.js";

export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  localStorage.setItem("access", response.data.access);
  localStorage.setItem("refresh", response.data.refresh);
  localStorage.setItem("user", JSON.stringify(response.data.user));
  return response.data.user;
}

export async function register({ name, email, password, tenantName }) {
  const payload = { name, email, password };
  if (tenantName) {
    payload.tenant_name = tenantName;
  }

  const response = await api.post("/auth/register", payload);
  localStorage.setItem("access", response.data.access);
  localStorage.setItem("refresh", response.data.refresh);
  localStorage.setItem("user", JSON.stringify(response.data.user));
  return response.data.user;
}

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
}

export function currentUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem("access"));
}
