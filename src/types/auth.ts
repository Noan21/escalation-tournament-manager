export type UserRole = "admin" | "staff" | "player";

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  email_verified_at: string | null;
  roles: UserRole[];
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface MagicLinkRequest {
  email: string;
}

export interface MagicLinkConsumeRequest {
  token: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ApiErrorPayload {
  detail?: string | string[] | Record<string, unknown>;
  [key: string]: unknown;
}
