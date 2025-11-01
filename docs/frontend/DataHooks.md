# Frontend Data Hooks Plan

React/Next.js (App Router) hooks for admin and player flows. Hooks wrap the REST endpoints defined in `docs/api/EndpointMap.md` and return typed data (using `@tanstack/react-query` or the Next.js `use` pattern). All examples assume TypeScript.

## 🧾 Shared Utilities

- `useApiClient()` – returns fetcher with base URL and auth headers.
- `useAuth()` – exposes session info (`user`, `roles`, `token`).
- `ApiError` – typed error object for consistent handling.

## 🎫 Registration Hooks

- `useEventRegistrations(eventId: UUID, { includeWaitlist?: boolean })`
  - GET `/api/registrations/events/{eventId}`
  - Returns `EventRegistration[]`
  - Stale time: 30s; refetch on focus.
- `useCreateRegistration(eventId: UUID)`
  - POST `/api/registrations/events/{eventId}`
  - Mutation payload: `EventRegistrationCreate`
  - Invalidates `useEventRegistrations`
- `useUpdateRegistrationStatus()`
  - PATCH `/api/registrations/{registrationId}/status`
  - Mutation payload: `{ status: RegistrationStatus }`
  - After success, refetch event registrations + standings.
- `useRecordCheckIn()`
  - POST `/api/registrations/{registrationId}/check-in`
  - Mutation payload: `CheckInRequest`
- `useSeedEventRoster(eventId: UUID)`
  - POST `/api/registrations/events/{eventId}/seed`
  - Admin-only; returns `SeedRosterResult`

## 🤝 Pairing Hooks

- `useGenerateRound(stageId: UUID)`
  - POST `/api/stages/{stageId}/pairings/rounds`
  - Payload: `GenerateRoundRequest`
  - Response: `RoundProfile`
  - On success, invalidate round list + standings.
- `usePreviewPairings(stageId: UUID)`
  - POST `/api/stages/{stageId}/pairings/rounds/preview`
  - Returns `PairingPreview`
- `useAssignTables(roundId: UUID)`
  - POST `/api/stages/{stageId}/pairings/rounds/{roundId}/assign-tables`
  - Payload: `AssignTablesRequest`

- `useStageRounds(stageId: UUID)`
  - GET `/api/stages/{stageId}/rounds` (to be implemented)
  - Returns `RoundProfile[]`

## 🧮 Scoring Hooks

- `useSubmitMatchResult()`
  - POST `/api/matches/{matchId}/result`
  - Payload: `MatchResultSubmit`
  - On success, refetch round + standings.
- `useLockRound(roundId: UUID)`
  - POST `/api/rounds/{roundId}/lock`
  - Response: `RoundProfile`
  - On success, refetch standings and notify summary.
- `useReopenRound(roundId: UUID)`
  - POST `/api/rounds/{roundId}/reopen`
  - Payload: `ReopenRoundRequest`

## 📈 Standings Hooks

- `useStageStandings(stageId: UUID, { refresh?: boolean })`
  - GET `/api/stages/{stageId}/standings`
  - Response: `StandingsPayload`
  - `refresh=true` triggers server recompute before returning.
- `useComputeStandings(stageId: UUID)`
  - POST `/api/stages/{stageId}/standings/compute`
  - Payload: optional `ComputeStandingsRequest`
- `usePublishStandings(stageId: UUID)`
  - POST `/api/stages/{stageId}/standings/publish`
  - Response: `StandingsPayload`

## 🗓️ Season Hooks

- `useCurrentSeason()`
  - GET `/api/seasons/current` (implement convenience endpoint)
  - Returns `SeasonProfile`
- `useSetCurrentSeason()`
  - POST `/api/seasons/{seasonId}/set-current`
- `useSeasonLeaderboard(seasonId: UUID)`
  - GET `/api/seasons/{seasonId}/leaderboard` (implement)
  - Returns `SeasonLeaderboard`
- `useRecomputeSeason(seasonId: UUID)`
  - POST `/api/seasons/{seasonId}/recompute`

## 📣 Notification Hooks

- `useNotificationPreferences(subjectId: UUID)`
  - GET `/api/notifications/preferences?subject_id=...`
- `useUpsertNotificationPreference()`
  - POST `/api/notifications/preferences`
- `useDispatchNotification()`
  - POST `/api/notifications/dispatch`
  - Admin-only manual send.

## 🧭 Orchestrator Hooks

- `useRunOrchestrator(eventId: UUID)`
  - POST `/api/orchestrator/events/{eventId}/run`
  - Payload: `OrchestratorCommand`
  - Response: `OrchestratorResult`
- `useAdvanceStage(stageId: UUID)`
  - POST `/api/orchestrator/stages/{stageId}/advance`

## ⚙️ Maintenance Hooks (Admin Console)

- `useRunCleanupJob()`
  - POST `/api/maintenance/run-cleanup`
- `useRunArchiveJob()`
  - POST `/api/maintenance/run-archive`
- `useRunMigrationJob()`
  - POST `/api/maintenance/run-migrations`
- `useMaintenanceHistory()`
  - GET `/api/maintenance/history` (optional table for past runs)

## 🔒 Auth Hooks

- `useRegister()`
  - POST `/api/auth/register`
- `useVerifyEmail()`
  - GET `/api/auth/verify-email` (triggered from route action)
- `useLogin()`, `useLogout()`, `useSession()`
  - Wrap `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
  - Session stored in cookies or secure storage.
- `useRequestMagicLink()`
  - POST `/api/auth/magic-link`
- `useConsumeMagicLink()`
  - POST `/api/auth/magic-link/consume`
- `useChangePassword()`
  - POST `/api/auth/change-password`

## UI Integration Notes

- Admin panels use `react-query` mutation side effects to navigate or toast success/failure.
- Player-facing pages (pairings, standings) poll via `refetchInterval` during rounds for near-real-time updates.
- Shared layout loads `useCurrentSeason()` and provides via React context.
- Error boundaries wrap sections with retries and fallback UI (e.g., “Failed to load standings, retry?”).
