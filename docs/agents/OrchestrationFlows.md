# Agent Orchestration Flows

Detailed sequences for each agent. These flows assume the service interfaces defined in `docs/services/ServiceInterfaces.md` and the data models under `docs/classes/`.

## 🧭 OrchestratorAgent

1. Receive command (admin UI, CLI, or automation) to run an event lifecycle step.
2. Fetch `EventProfile` + associated `StageConfig` via Season/Event services.
3. Determine next action based on event state:
   - Stage creation → call `RegistrationService.seed_event_roster`.
   - Generate round → delegate to `PairingAgent`.
   - Lock round → delegate to `ScoringAgent` then `StandingAgent`.
   - Finalize event → ensure standings published, trigger `SeasonAgent`.
4. Record audit log entry with `actor_id`, event/stage, action performed.
5. Optionally queue notifications via `NotificationAgent` when significant milestones occur.

## 📝 RegistrationAgent

1. Triggered when an event moves into registration or when roster seeding is requested.
2. Load event, season, and organization defaults.
3. Validate incoming participant/team payloads against `ParticipantProfile` / `TeamProfile`.
4. For each participant/team:
   - Check existing registration status.
   - Create new `EventRegistration` or update existing record via `RegistrationService`.
5. If check-in requested, record `CheckInRecord` with appropriate method.
6. Return summary (counts created, updated, skipped) to caller.

## 🤝 PairingAgent

1. Triggered by `POST /stages/{id}/rounds` or orchestrator command.
2. Retrieve `StageConfig`, prior `RoundProfile` data, and relevant `MatchProfile` records.
3. Resolve `TournamentFormatConfig` via `tournament_formats` registry.
4. Build pairing pool (list of eligible registrations with points, breakers).
5. Execute format’s pairing strategy (e.g., Swiss) to produce matchups:
   - Respect pairing seed if provided.
   - Handle byes, avoid repeats if config requires.
6. Persist `RoundProfile` and `MatchProfile` rows:
   - Use `PairingService.generate_round_pairings`.
   - Assign default table numbers (sequential) unless overridden.
7. Update round status to `pairing` or `active` depending on config.
8. Return newly created `RoundProfile` with matches for display and notifications.

## 🧮 ScoringAgent

1. Triggered by `POST /rounds/{id}/lock` or admin result submission.
2. When handling individual match results:
   - Accept `MatchResultSubmit`.
   - Validate wins/draw totals against allowed format (e.g., best-of-three).
   - Update `MatchProfile` state to `completed` with recalculated `MatchScore`.
3. When locking a round:
   - Ensure every non-bye match is completed; reject otherwise.
   - Set `RoundProfile.status = "locked"` and stamp lock timestamp.
   - Invoke `StandingAgent.compute_stage_standings`.
4. Post-lock, notify participants via `NotificationAgent` if configured.
5. Return updated `RoundProfile` (and optionally the standings snapshot).

## 📈 StandingAgent

1. Triggered after `ScoringAgent` locks a round or upon manual recompute.
2. Load `StageConfig`, `ScoringProfile`, and all relevant matches.
3. Compute match points using `ResultPoints` (win/draw/loss/byes).
4. Calculate tiebreakers in defined order (opponent win %, head-to-head, score diff).
5. Update `standings` table with ranks, metrics, and `breakers_applied`.
6. Capture `TiebreakSnapshot` rows for audit.
7. Optionally mark standings as published if requested.
8. Return `StandingsPayload`.

## 🗓️ SeasonAgent

1. Triggered at event completion or on scheduled recompute (nightly).
2. Retrieve `SeasonProfile` + `SeasonStandingConfig`.
3. Gather eligible events + stage standings (respect include/exclude lists).
4. Aggregate points per participant/team, applying drop-lowest/min-events rules.
5. Persist season leaderboard (separate table or materialized view depending on implementation).
6. Update season metadata (last computed timestamp) and return `SeasonLeaderboard`.
7. Queue notifications for season updates if relevant.

## 📣 NotificationAgent

1. Triggered after pairing, round lock, or season updates (or manual send).
2. Determine recipients by querying `notification_preferences`.
3. Filter channels based on triggers, mute windows, and rate limits.
4. Render message templates (context: event, round, standings).
5. Dispatch to delivery providers (email, Discord, Slack) and log each `NotificationDelivery`.
6. Handle retries for failed deliveries according to policy.

## 🧹 MaintenanceAgent

1. Runs on schedule (e.g., nightly).
2. Load active `cleanup_policies`, `archive_policies`, and `migration_policies`.
3. For each cleanup policy:
   - Execute pruning queries (e.g., delete stale registrations older than retention).
4. For archive policies:
   - Identify events past threshold; apply chosen mode (soft delete/export).
5. For migration policies flagged `run_on_startup` or scheduled:
   - Execute pending migrations or maintenance tasks; record status.
6. Emit summary logs/notifications if desired.

---

These flows, combined with the service interfaces and models, provide a clear blueprint for implementing each agent in FastAPI background tasks or CLI commands.
