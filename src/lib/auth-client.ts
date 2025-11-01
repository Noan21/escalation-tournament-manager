import { apiFetch } from "@/lib/api-client";
import type {
  AuthTokens,
  ChangePasswordRequest,
  LoginRequest,
  MagicLinkConsumeRequest,
  MagicLinkRequest,
  RegisterRequest,
  RefreshRequest,
  UserProfile,
} from "@/types/auth";

export const register = (payload: RegisterRequest): Promise<UserProfile> =>
  apiFetch<UserProfile>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const login = (payload: LoginRequest): Promise<AuthTokens> =>
  apiFetch<AuthTokens>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const refresh = (
  payload: RefreshRequest,
  authToken?: string | null
): Promise<AuthTokens> =>
  apiFetch<AuthTokens>("/api/auth/refresh", {
    method: "POST",
    body: JSON.stringify(payload),
    authToken,
  });

export const fetchProfile = (authToken: string): Promise<UserProfile> =>
  apiFetch<UserProfile>("/api/auth/me", {
    method: "GET",
    authToken,
  });

export const requestMagicLink = (payload: MagicLinkRequest): Promise<void> =>
  apiFetch<void>("/api/auth/magic-link", {
    method: "POST",
    body: JSON.stringify(payload),
    parseJson: false,
  });

export const consumeMagicLink = (payload: MagicLinkConsumeRequest): Promise<AuthTokens> =>
  apiFetch<AuthTokens>("/api/auth/magic-link/consume", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const changePassword = (
  authToken: string,
  payload: ChangePasswordRequest
): Promise<void> =>
  apiFetch<void>("/api/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
    authToken,
    parseJson: false,
  });

export const logout = (authToken: string, payload: RefreshRequest): Promise<void> =>
  apiFetch<void>("/api/auth/logout", {
    method: "POST",
    body: JSON.stringify(payload),
    authToken,
    parseJson: false,
  });
