# Background Scheduling Plan

Guidance for recurring jobs and asynchronous workers. Jobs can be orchestrated via Celery, Dramatiq, APScheduler, or a lightweight cron runner—this document focuses on cadence and responsibilities rather than technology choice.

## ⏰ Scheduler Overview

- **Crontab notation** assumes UTC.
- Jobs run against the FastAPI app’s service layer/agents, passing `actor_id=None` or a system user.
- Use DigitalOcean’s App Platform jobs, systemd timers, or a dedicated worker process depending on deployment.

## 🧹 MaintenanceAgent Jobs

| Job | Cron | Description |
| --- | --- | --- |
| `cleanup-nightly` | `0 3 * * *` | Runs `MaintenanceAgent` cleanup policies (stale registrations, expired auth tokens, logs, notification delivery pruning). |
| `archive-weekly` | `0 4 * * MON` | Applies archive policies to completed events beyond retention windows. |
| `migration-check` | `*/30 * * * *` | Checks `migration_policies` for pending work; lightweight query to queue long-running tasks if needed. |

Implementation steps:
1. Scheduler triggers HTTP endpoint `/api/maintenance/run-cleanup` (with admin API token) or runs an internal worker call.
2. Jobs log summary of deleted/archived rows and last-run timestamps.

## 📣 NotificationAgent Jobs

| Job | Cron | Description |
| --- | --- | --- |
| `notify-pairings` | `*/5 * * * *` | Polls for rounds that have freshly generated pairings but unsent notifications. |
| `notify-standings` | `*/10 * * * *` | Sends standings updates for stages flagged as published since last poll. |
| `notify-season` | `30 2 * * *` | Sends nightly digest of season leaderboard movements (optional). |

Implementation notes:
- Workers query `notification_preferences` to respect muted settings and rate limits.
- For low volume, a simple background task after each event (pairing/lock) may suffice; cron jobs ensure retries if synchronous tasks fail.

## 🗓️ SeasonAgent Jobs

| Job | Cron | Description |
| --- | --- | --- |
| `season-recompute` | `15 2 * * *` | Recomputes the current season leaderboard nightly. |
| `season-snapshot` | `0 1 * * MON` | Generates a weekly snapshot/export for archives (optional future enhancement). |

Workflow:
1. Scheduler calls `/api/seasons/{season_id}/recompute`.
2. After recompute, optionally trigger `NotificationAgent` for summary emails/webhooks.
3. Store `SeasonAgent` outputs with timestamp for audit.

## ⚠️ Failure Handling

- Use idempotent jobs: each agent operation should safely re-run without duplicating side effects.
- Maintain a `job_runs` table or external log to capture status (success/failure, duration, errors).
- Consider alerting (e.g., Slack, email) when maintenance or recompute jobs fail more than N consecutive times.

## 🚀 Manual Triggers

- Admin UI should expose “Run now” buttons invoking the same endpoints with elevated auth.
- CLI scripts (e.g., `python -m app.maintenance.run`) can run standalone for debugging or initial seeding.

## 🔐 Credentials & Security

- Scheduler credentials should be long-lived tokens with `admin` privileges scoped to maintenance endpoints.
- Rotate tokens periodically and store them securely (DO App secrets, Vault, etc.).
