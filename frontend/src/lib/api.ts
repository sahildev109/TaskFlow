import axios from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = Cookies.get("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          Cookies.set("access_token", data.access_token, { secure: true, sameSite: "strict" });
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authAPI = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),
};

// ── Tasks ─────────────────────────────────────────────────────────────────────

export const tasksAPI = {
  list: (params?: { page?: number; page_size?: number; status?: string; priority?: string; search?: string }) =>
    api.get("/tasks/", { params }),
  get: (id: string) => api.get(`/tasks/${id}`),
  create: (data: { title: string; description?: string; status?: string; priority?: string; due_date?: string }) =>
    api.post("/tasks/", data),
  update: (id: string, data: Partial<{ title: string; description: string; status: string; priority: string; due_date: string }>) =>
    api.patch(`/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
};
