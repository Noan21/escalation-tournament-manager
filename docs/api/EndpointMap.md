# API Endpoint Map

FastAPI route plan aligned with the service interfaces documented in `docs/services/ServiceInterfaces.md`. All endpoints return or accept the Pydantic models defined under `docs/classes/`. Authentication uses token-based headers (e.g., `Authorization: Bearer <token>`), with role checks (`admin`, `staff`, `player`).

## Auth conventions

- `admin`: full control over event lifecycle, seasons, maintenance.
- `staff`: can manage registrations, pairings, scoring, but not global settings.
- `player`: read-only access to public data and their own registrations.

## 🎫 Registration Routes (`/api/registrations`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/events/{event_id}` | `create_registration` | `player` or `admin` | `EventRegistrationCreate` | `EventRegistration` |
| PATCH | `/{registration_id}/status` | `update_registration_status` | `admin` or `staff` | `UpdateRegistrationStatus` | `EventRegistration` |
| GET | `/events/{event_id}` | `list_event_registrations` | `staff` | query: `include_waitlist: bool` | `list[EventRegistration]` |
| POST | `/{registration_id}/check-in` | `record_check_in` | `staff` | `CheckInRequest` | `CheckInRecord` |
| POST | `/events/{event_id}/seed` | `seed_event_roster` | `admin` | none | `SeedRosterResult` |

## 🤝 Pairing Routes (`/api/stages/{stage_id}/pairings`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/rounds` | `generate_round_pairings` | `admin` or `staff` | `GenerateRoundRequest` | `RoundProfile` |
| POST | `/rounds/preview` | `preview_pairings` | `staff` | `GenerateRoundRequest` | `PairingPreview` |
| POST | `/rounds/{round_id}/assign-tables` | `assign_tables` | `staff` | `AssignTablesRequest` | `RoundProfile` |

## 🧮 Scoring Routes (`/api/matches` & `/api/rounds`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/{match_id}/result` | `submit_match_result` | `staff` or authorized `player` | `MatchResultSubmit` | `MatchProfile` |
| POST | `/api/rounds/{round_id}/lock` | `lock_round` | `staff` | none | `RoundProfile` |
| POST | `/api/rounds/{round_id}/reopen` | `reopen_round` | `admin` | `ReopenRoundRequest` | `RoundProfile` |

## 📈 Standings Routes (`/api/stages/{stage_id}/standings`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/compute` | `compute_stage_standings` | `staff` | optional: `ComputeStandingsRequest` | `StandingsPayload` |
| GET | `/` | `get_stage_standings` | `player` (public if published) | query: `refresh: bool` | `StandingsPayload` |
| POST | `/publish` | `publish_stage_standings` | `admin` | none | `StandingsPayload` |

## 🗓️ Season Routes (`/api/seasons`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/{season_id}/set-current` | `set_current_season` | `admin` | none | `SeasonProfile` |
| POST | `/{season_id}/recompute` | `recompute_season_leaderboard` | `admin` | none | `SeasonLeaderboard` |
| GET | `/{season_id}/events` | `list_season_events` | `player` | query: `status` | `list[EventProfile]` |

## ⚙️ Maintenance Routes (`/api/maintenance`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/run-cleanup` | trigger cleanup policies | `admin` | optional: `CleanupTriggerRequest` | `MaintenanceSummary` |
| POST | `/run-archive` | trigger archive policies | `admin` | optional: `ArchiveTriggerRequest` | `MaintenanceSummary` |
| POST | `/run-migrations` | trigger migration policies | `admin` | optional: `MigrationTriggerRequest` | `MaintenanceSummary` |

## 📣 Notification Routes (`/api/notifications`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/preferences` | list preferences | `admin` or same subject | query: `subject_id` | `list[NotificationPreference]` |
| POST | `/preferences` | create/update preference | `admin` or subject | `NotificationPreferenceUpsert` | `NotificationPreference` |
| POST | `/dispatch` | trigger notification send | `admin` | `NotificationDispatchRequest` | `list[NotificationDelivery]` |

## 🧭 Orchestrator Routes (`/api/orchestrator`)

| Method | Path | Handler | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/events/{event_id}/run` | run orchestration step | `admin` | `OrchestratorCommand` | `OrchestratorResult` |
| POST | `/stages/{stage_id}/advance` | advance stage | `admin` | `AdvanceStageRequest` | `StageConfig` |

## 🚦 Auth & Session (`/api/auth`)

| Method | Path | Purpose | Auth | Request Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/register` | create account | public | `RegisterRequest` | `UserProfile` |
| GET | `/verify-email` | confirm email via token | public | query: `token` | Redirect or 204 |
| POST | `/login` | username/password login | public | `LoginRequest` | `AuthTokens` |
| POST | `/logout` | revoke refresh token | authenticated | `LogoutRequest` | 204 |
| POST | `/refresh` | issue new access token | authenticated | `RefreshRequest` | `AuthTokens` |
| POST | `/magic-link` | send magic login link | public | `MagicLinkRequest` | 202 |
| POST | `/magic-link/consume` | consume magic link | public | `MagicLinkConsumeRequest` | `AuthTokens` |
| POST | `/change-password` | change password | authenticated | `ChangePasswordRequest` | 204 |
| GET | `/me` | current session profile | authenticated | — | `SessionProfile` |

## 🧾 Supporting DTOs

- `UpdateRegistrationStatus`: `{ "status": "confirmed" }`
- `CheckInRequest`: `{ "method": "admin_manual", "note": "Walk-in" }`
- `GenerateRoundRequest`: `{ "round_number": 3, "pairing_seed": "..." }`
- `AssignTablesRequest`: list of `{ "match_id": UUID, "table_number": int }`
- `ReopenRoundRequest`: `{ "reason": "Score correction" }`
- `ComputeStandingsRequest`: optional override scoring profile key.
- `NotificationDispatchRequest`: trigger manual notifications (e.g., `{"trigger": "round_pairings", "stage_id": ...}`)
- `OrchestratorCommand`: describes which action to execute (generate round, lock round, finalize event).
- `RegisterRequest`: `{ "username": "player1", "email": "player1@example.com", "password": "strongpass123" }`
- `LoginRequest`: `{ "username": "player1", "password": "strongpass123" }`
- `AuthTokens`: `{ "access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 900 }`
- `MagicLinkRequest`: `{ "email": "player1@example.com" }`
- `MagicLinkConsumeRequest`: `{ "token": "..." }`
- `ChangePasswordRequest`: `{ "current_password": "...", "new_password": "..." }`
- `LogoutRequest`: `{ "refresh_token": "..." }`
- `RefreshRequest`: `{ "refresh_token": "..." }`

Auth enforcement will live in FastAPI dependencies (`Depends(get_current_user)` etc.), checking role claims before invoking service methods. Error responses follow FastAPI defaults (422 for validation errors, 403 for forbidden, 404 for missing resources).
