import axios, {
  type AxiosInstance,
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";
import type { ApiError } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { tokens } = useAuthStore.getState();

    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }

    // Add request ID for tracking
    config.headers["X-Request-ID"] = crypto.randomUUID();

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const { addNotification } = useNotificationStore.getState();
    const { logout } = useAuthStore.getState();

    // Handle 401 Unauthorized - Auto logout
    if (error.response?.status === 401) {
      logout();
      addNotification({
        type: "error",
        title: "Session expired",
        message: "Please login again",
      });
      window.location.href = "/login";
      return Promise.reject(error);
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      addNotification({
        type: "error",
        title: "Access denied",
        message: "You do not have permission to perform this action",
      });
    }

    // Handle 429 Rate Limit
    if (error.response?.status === 429) {
      addNotification({
        type: "warning",
        title: "Rate limit exceeded",
        message: "Too many requests. Please try again later.",
      });
    }

    // Handle 500+ Server errors
    if (error.response && error.response.status >= 500) {
      addNotification({
        type: "error",
        title: "Server error",
        message: error.response.data?.detail || "An unexpected error occurred",
      });
    }

    return Promise.reject(error);
  },
);

// Helper functions
export async function get<T>(url: string, config = {}) {
  const response = await apiClient.get<T>(url, config);
  return response.data;
}

export async function post<T>(url: string, data?: unknown, config = {}) {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
}

export async function put<T>(url: string, data?: unknown, config = {}) {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
}

export async function patch<T>(url: string, data?: unknown, config = {}) {
  const response = await apiClient.patch<T>(url, data, config);
  return response.data;
}

export async function del<T>(url: string, config = {}) {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
}
