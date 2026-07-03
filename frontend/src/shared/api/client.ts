import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import { tokenStore } from "./tokens";
import type { ApiError } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// --- request: attach JWT access token --------------------------------------- //
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// --- response: refresh once on 401, normalize errors ------------------------ //
let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${BASE_URL}/auth/token/refresh`, { refresh });
    tokenStore.setAccess(data.access);
    if (data.refresh) tokenStore.setRefresh(data.refresh);
    return data.access as string;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean };

    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      refreshing = refreshing ?? refreshAccess();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess) {
        original.headers.set("Authorization", `Bearer ${newAccess}`);
        return api(original);
      }
      // refresh failed → bubble up so the auth layer can redirect to login
      window.dispatchEvent(new CustomEvent("arkand:logout"));
    }
    return Promise.reject(toApiError(error));
  },
);

/** Normalize any axios error into our { code, message, details } contract. */
export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    if (data && data.code && data.message) return data;
    return {
      code: "network_error",
      message: error.message || "Ошибка сети",
      details: {},
    };
  }
  return { code: "unknown", message: "Неизвестная ошибка", details: {} };
}
