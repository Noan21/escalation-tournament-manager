import { getApiBaseUrl } from "@/lib/env";
import type { ApiErrorPayload } from "@/types/auth";

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | undefined;

  constructor(status: number, message: string, payload?: ApiErrorPayload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export interface ApiFetchOptions extends RequestInit {
  authToken?: string | null;
  parseJson?: boolean;
}

export async function apiFetch<T>(
  path: string,
  { authToken, parseJson = true, headers, ...init }: ApiFetchOptions = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = path.startsWith("http") ? path : `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;

  const requestHeaders = new Headers(headers ?? {});
  if (authToken) {
    requestHeaders.set("Authorization", `Bearer ${authToken}`);
  }

  if (init.body && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...init,
    headers: requestHeaders,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      // Ignore JSON parsing errors and fall back to default message
    }
    const message = payload?.detail
      ? Array.isArray(payload.detail)
        ? payload.detail.join(", ")
        : String(payload.detail)
      : response.statusText || "Request failed";
    throw new ApiError(response.status, message, payload);
  }

  if (!parseJson) {
    return undefined as T;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
