# Authentication Plan

Application-specific username/password auth with email verification and optional magic-link login. No third-party identity provider.

## 🔐 Credentials

- `username`: unique, min length 3, stored lowercase.
- `email`: required, must be verified before full access; used for magic links.
- `password_hash`: stored using Argon2id via `passlib` (`argon2-cffi` backend). Passwords never stored in plain text.
- Password policy: minimum 12 characters, enforce at validation layer.

## 📦 Suggested Libraries

- `passlib[argon2]` for secure hashing/verification.
- `python-jose` or `PyJWT` for signing access/refresh tokens.
- `itsdangerous` for time-bound signed email verification & magic-link tokens (alternatively use JWT with dedicated claims).
- `aiosmtplib` or transactional email API (SendGrid, Mailgun) for sending verification & magic-link emails.

## 🗃️ Database Tables

Add to PostgreSQL schema (see `docs/database/DatabaseSchema.md`):

- `users`: core identity (id, username, email, email_verified_at, password_hash, roles, last_login_at, created_at, updated_at).
- `email_verification_tokens`: store issued tokens with expiry.
- `magic_link_tokens`: single-use tokens for passwordless login; include request metadata (ip, user_agent) for auditing.
- `sessions` (optional): refresh tokens or persistent sessions for revocation.
- `password_reset_tokens`: optional separate table if we later support password reset distinct from magic links.

All token tables should store `hashed_token` (e.g., SHA-256 of the raw token) to avoid storing raw secrets.

## 🔄 Flows

### Registration
1. User submits `username`, `email`, `password`.
2. Validate uniqueness and password strength.
3. Hash password with Argon2id; insert into `users` with `email_verified_at = NULL`.
4. Generate email verification token (signed string), store hashed version, send verification email.
5. Return 201 with limited session token or require verification before login (configurable).

### Email Verification
1. User clicks verification link (`GET /api/auth/verify-email?token=...`).
2. Verify signature + expiry; look up hashed token in table.
3. Mark `email_verified_at` and delete token.
4. Optionally issue new auth tokens or redirect to login.

### Username/Password Login
1. User submits `username` (or email) + password.
2. Look up user, verify password via `passlib`.
3. Reject if `email_verified_at` is null (return 403 with “verify email” message).
4. Issue access token (JWT 15m) + refresh token (JWT 7d) or session entry.
5. Record `last_login_at`, store refresh token hash if using DB-backed sessions.

### Magic Link Login
1. User enters verified email.
2. Generate time-bound token (10–15 min), store hashed token in `magic_link_tokens` with single-use flag.
3. Email link (`https://app/.../magic-login?token=...`).
4. On consumption, verify token, mark consumed, issue auth tokens as in password login.
5. Optionally prompt user to set password if none exists.

### Password Change
1. Authenticated user submits current password + new password.
2. Verify current password, hash new password, update `password_hash`, invalidate existing sessions.

### Logout / Token Revocation
- Access tokens are stateless; rely on refresh tokens/sessions:
  - Maintain `sessions` table with `refresh_token_hash`, device info, expiry.
  - Logout deletes session entry; server rejects unknown tokens.

## 🛡️ Security Considerations

- Rate limit login and magic-link requests (e.g., 5 per 15 min per IP/email).
- Throttle email sends to prevent abuse.
- Use HTTPS end-to-end (already handled via Cloudflare/Nginx).
- Sign tokens with strong secrets stored in environment variables.
- Implement account lockout or exponential back-off on repeated failed login attempts.
- Log authentication events for audit.

## 🧪 Testing

- Integration tests hit the real Postgres test database for registration → verification → login and magic-link flows.
- Validate password hashing and token expiry through end-to-end scenarios (no isolated unit tests).

## 🗂️ Implementation Outline

1. Create `app/services/auth.py` implementing `AuthService`.
2. Add FastAPI routes under `/api/auth`:
   - `POST /register`
   - `POST /login`
   - `POST /magic-link`
   - `POST /magic-link/consume`
   - `GET /verify-email`
   - `POST /change-password`
   - `POST /logout`
3. Integrate with middleware/dependencies to extract user/roles from access token.
4. Update frontend hooks (`useLogin`, `useMagicLink`, `useVerifyEmail`, etc.).
