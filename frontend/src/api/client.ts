/**
 * Unified API Client for DocMind Frontend
 * Handles base URL configuration, request headers, JSON parsing, and unified error handling.
 */

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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  data?: unknown;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { data, headers: customHeaders, ...customOptions } = options;

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  let body: BodyInit | null | undefined = customOptions.body;

  if (data !== undefined) {
    if (data instanceof FormData) {
      body = data;
      // Trình duyệt tự set Content-Type cùng boundary cho FormData
    } else {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(data);
    }
  }

  const finalHeaders = {
    ...headers,
    ...(customHeaders as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...customOptions,
      headers: finalHeaders,
      body,
    });

    if (response.status === 204) {
      return undefined as T;
    }

    const contentType = response.headers.get("content-type");
    const isJson = contentType && contentType.includes("application/json");
    const payload = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      let errorMessage = `Yêu cầu thất bại với mã trạng thái ${response.status}`;
      if (typeof payload === "object" && payload !== null) {
        if ("detail" in payload) {
          const detail = (payload as { detail: unknown }).detail;
          errorMessage = typeof detail === "string" ? detail : JSON.stringify(detail);
        } else if ("message" in payload) {
          errorMessage = String((payload as { message: unknown }).message);
        }
      } else if (typeof payload === "string" && payload.trim().length > 0) {
        errorMessage = payload;
      }

      throw new ApiError(errorMessage, response.status, payload);
    }

    return payload as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }

    const networkMessage =
      err instanceof Error
        ? `Không thể kết nối đến máy chủ backend: ${err.message}`
        : "Lỗi kết nối mạng đến máy chủ backend.";

    throw new ApiError(networkMessage, 0);
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: "POST", data }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: "DELETE" }),
};
