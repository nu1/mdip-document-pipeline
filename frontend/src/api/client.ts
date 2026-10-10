import type { ApiErrorDetail } from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Base fetch wrapper with typed responses and error parsing.
 */
export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const response = await fetch(url, options);

  if (!response.ok) {
    let errorDetail: string | undefined;
    let data: unknown;

    try {
      data = await response.json();
      const errorJson = data as ApiErrorDetail;
      if (typeof errorJson?.detail === "string") {
        errorDetail = errorJson.detail;
      } else if (typeof errorJson?.message === "string") {
        errorDetail = errorJson.message;
      }
    } catch {
      // response body is not JSON, ignore
    }

    const message =
      errorDetail || `Request failed with status ${response.status} (${response.statusText || "Error"}).`;
    throw new ApiError(message, response.status, data);
  }

  return response.json() as Promise<T>;
}
