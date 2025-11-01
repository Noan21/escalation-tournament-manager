const DEFAULT_API_BASE_URL = "http://localhost:8000";

const trimTrailingSlash = (value: string): string =>
  value.endsWith("/") ? value.slice(0, -1) : value;

export const getApiBaseUrl = (): string => {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE_URL) {
    return trimTrailingSlash(process.env.NEXT_PUBLIC_API_BASE_URL);
  }
  return DEFAULT_API_BASE_URL;
};
