# Database Schema

PostgreSQL 17 database design for the single-organization tournament platform. All primary keys are UUIDs (`gen_random_uuid()`), timestamps are stored in UTC, and soft deletes are avoided in favor of archival tables/policies.

## 📦 Core Reference Tables

### `users`

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | uuid | pk | |
| `username` | text | unique not null | Stored lowercase. |
| `email` | text | unique not null | |
| `email_verified_at` | timestamptz | nullable | |
| `password_hash` | text | not null | Argon2id hash. |
| `roles` | text[] | not null default `'{player}'` | e.g., `{admin,staff}`. |
| `last_login_at` | timestamptz | nullable | |
| `meta` | jsonb | not null default `'{}'` | |
| `created_at` / `updated_at` | timestamptz | not null | |

Optional index: `CREATE INDEX ON users ((lower(username)));`

### `organizations`

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | uuid | pk | Singleton row representing the owning organization. |
| `name` | text | not null | Display name. |
| `slug` | text | unique | URL-friendly identifier. |
| `visibility` | text | check in (`private`,`unlisted`,`public`) | Controls public exposure. |
| `contact_email` | text | nullable | Admin contact. |
| `website` | text | nullable | Optional URL. |
| `discord_url` | text | nullable | Optional community URL. |
| `timezone` | text | not null | IANA zone. |
| `meta` | jsonb | not null default `'{}'` | Arbitrary metadata. |
| `created_at` / `updated_at` | timestamptz | not null | Managed timestamps. |

### `seasons`

| Column | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | uuid | pk | |
| `organization_id` | uuid | fk → `organizations.id` | Always references singleton org. |
| `name` | text | not null | |
| `slug` | text | unique | |
| `year` | int | not null | Display grouping. |
| `status` | text | check in (`planning`,`active`,`complete`,`archived`) | |
| `is_current` | bool | not null default false | Exactly one row true. |
| `starts_on` / `ends_on` | timestamptz | not null | Season bounds. |
| `description` | text | nullable | |
| `leaderboard_url` | text | nullable | External link if published. |
| `meta` | jsonb | not null default `'{}'` | |
| `created_at` / `updated_at` | timestamptz | not null | |

Index: `unique (organization_id, is_current) where is_current` to enforce single active season.

## 👤 Participants & Teams

### `participants`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `organization_id` | uuid | fk → `organizations.id` |
| `display_name` | text | not null |
| `status` | text | check in (`active`,`suspended`,`retired`) |
| `email` | text | nullable |
| `handles` | jsonb | not null default `'[]'` |
| `meta` | jsonb | not null default `'{}'` |
| `created_at` / `updated_at` | timestamptz | not null |

`handles` stores array of `{kind,value}` objects.

### `teams`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `organization_id` | uuid | fk |
| `name` | text | not null |
| `status` | text | check in (`active`,`inactive`) |
| `handles` | jsonb | not null default `'[]'` |
| `meta` | jsonb | not null default `'{}'` |
| `created_at` / `updated_at` | timestamptz | not null |

### `team_members`

| Column | Type | Constraints |
| --- | --- | --- |
| `team_id` | uuid | fk → `teams.id` |
| `participant_id` | uuid | fk → `participants.id` |
| `role` | text | check in (`captain`,`member`,`alternate`) default `member` |
| `joined_at` | timestamptz | not null |

Primary key: `(team_id, participant_id)`.

## 🔐 Authentication Support Tables

### `email_verification_tokens`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk → `users.id` |
| `token_hash` | text | unique not null |
| `expires_at` | timestamptz | not null |
| `created_at` | timestamptz | not null |

### `magic_link_tokens`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk → `users.id` |
| `token_hash` | text | unique not null |
| `expires_at` | timestamptz | not null |
| `consumed_at` | timestamptz | nullable |
| `request_ip` | inet | nullable |
| `user_agent` | text | nullable |
| `created_at` | timestamptz | not null |

Create partial unique index on `token_hash` where `consumed_at IS NULL`.

### `sessions`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk → `users.id` |
| `refresh_token_hash` | text | unique not null |
| `device_name` | text | nullable |
| `ip_address` | inet | nullable |
| `expires_at` | timestamptz | not null |
| `revoked_at` | timestamptz | nullable |
| `created_at` | timestamptz | not null |

### `password_reset_tokens` *(optional)*

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `user_id` | uuid | fk → `users.id` |
| `token_hash` | text | unique not null |
| `expires_at` | timestamptz | not null |
| `consumed_at` | timestamptz | nullable |
| `created_at` | timestamptz | not null |

## 🗓️ Events & Stages

### `events`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `season_id` | uuid | fk → `seasons.id` |
| `organization_id` | uuid | fk → `organizations.id` |
| `name` | text | not null |
| `slug` | text | unique |
| `status` | text | enum (`draft`,`registration`,`active`,`complete`,`archived`) |
| `starts_at` / `ends_at` | timestamptz | not null |
| `registration_opens_at` / `registration_closes_at` | timestamptz | not null |
| `registration_capacity` | int | nullable |
| `waitlist_enabled` | bool | not null default false |
| `auto_promote_waitlist` | bool | not null default false |
| `default_format_key` | text | not null |
| `default_scoring_key` | text | not null |
| `location_name` | text | nullable |
| `location_url` | text | nullable |
| `max_rounds_override` | int | nullable |
| `published_at` | timestamptz | nullable |
| `meta` | jsonb | not null default `'{}'` |
| `created_at` / `updated_at` | timestamptz | not null |

Index: `(season_id, starts_at)` for listing.

### `stages`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `event_id` | uuid | fk → `events.id` |
| `order` | int | not null |
| `name` | text | not null |
| `status` | text | enum (`pending`,`in_progress`,`complete`) |
| `format_key` | text | nullable |
| `scoring_key` | text | nullable |
| `round_count` | int | nullable |
| `advance_top` | int | nullable |
| `drop_cut` | int | nullable |
| `start_after_stage_id` | uuid | nullable fk → `stages.id` |
| `config` | jsonb | not null default `'{}'` |
| `created_at` / `updated_at` | timestamptz | not null |

Unique: `(event_id, order)`.

## 📝 Registration & Attendance

### `registrations`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `event_id` | uuid | fk → `events.id` |
| `subject_type` | text | enum (`participant`,`team`) |
| `participant_id` | uuid | nullable fk → `participants.id` |
| `team_id` | uuid | nullable fk → `teams.id` |
| `status` | text | enum (`pending`,`confirmed`,`checked_in`,`withdrawn`) |
| `seeding_score` | numeric | nullable |
| `notes` | text | nullable |
| `registered_at` | timestamptz | not null |
| `confirmed_at` / `checked_in_at` | timestamptz | nullable |
| `meta` | jsonb | not null default `'{}'` |

Constraints:
- Ensure exactly one of `participant_id` or `team_id` is present.
- Unique `(event_id, participant_id)` where `participant_id` not null.
- Unique `(event_id, team_id)` where `team_id` not null.

### `check_ins`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `registration_id` | uuid | fk → `registrations.id` |
| `recorded_by` | uuid | nullable fk → `participants.id` |
| `method` | text | enum (`self_service`,`admin_manual`,`kiosk`) |
| `note` | text | nullable |
| `recorded_at` | timestamptz | not null |

## 🔁 Rounds & Matches

### `rounds`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `stage_id` | uuid | fk → `stages.id` |
| `number` | int | not null |
| `status` | text | enum (`scheduled`,`pairing`,`active`,`locked`,`published`) |
| `pairings_released_at` | timestamptz | nullable |
| `games_start_at` | timestamptz | nullable |
| `submissions_due_at` | timestamptz | nullable |
| `locked_at` | timestamptz | nullable |
| `published_at` | timestamptz | nullable |
| `pairing_seed` | text | nullable |
| `notes` | text | nullable |
| `created_at` / `updated_at` | timestamptz | not null |

Unique: `(stage_id, number)`.

### `matches`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `round_id` | uuid | fk → `rounds.id` |
| `pairing_order` | int | not null |
| `state` | text | enum (`scheduled`,`in_progress`,`completed`,`bye`,`forfeit`,`cancelled`) |
| `table_number` | int | nullable |
| `judge_id` | uuid | nullable fk → `participants.id` |
| `stream_url` | text | nullable |
| `slot_a_participant_id` / `slot_b_participant_id` | uuid | nullable fk → `participants.id` |
| `slot_a_team_id` / `slot_b_team_id` | uuid | nullable fk → `teams.id` |
| `slot_a_seed` / `slot_b_seed` | int | nullable |
| `wins_a` / `wins_b` | int | not null default 0 |
| `draws` | int | not null default 0 |
| `total_points_a` / `total_points_b` | int | not null default 0 |
| `reported_by` / `confirmed_by` | uuid | nullable fk → `participants.id` |
| `reported_at` / `confirmed_at` | timestamptz | nullable |
| `meta` | jsonb | not null default `'{}'` |
| `created_at` / `updated_at` | timestamptz | not null |

Constraint: ensure exactly one of participant/team IDs per slot.

### `match_games`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `match_id` | uuid | fk → `matches.id` |
| `game_number` | int | not null |
| `outcome` | text | enum (`win_a`,`win_b`,`draw`,`pending`) |
| `score_a` / `score_b` | int | nullable |
| `completed_at` | timestamptz | nullable |
| `notes` | text | nullable |

Unique: `(match_id, game_number)`.

## 📊 Standings & Season Aggregates

### `standings`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `stage_id` | uuid | fk → `stages.id` |
| `subject_type` | text | enum (`participant`,`team`) |
| `subject_id` | uuid | not null |
| `rank` | int | not null |
| `match_points` | int | not null default 0 |
| `wins` / `losses` / `draws` | int | not null default 0 |
| `byes` | int | not null default 0 |
| `total_score` | int | not null default 0 |
| `strength_of_schedule` | numeric | nullable |
| `opponent_match_win_pct` | numeric | nullable |
| `head_to_head` | text | enum (`ahead`,`behind`,`tied`) nullable |
| `breakers_applied` | jsonb | not null default `'[]'` |
| `updated_at` | timestamptz | not null |

Unique: `(stage_id, subject_type, subject_id)`.

### `tiebreak_snapshots`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `standings_id` | uuid | fk → `standings.id` |
| `breaker_key` | text | not null |
| `value` | numeric | not null |
| `order_applied` | int | not null |
| `subject_ids` | uuid[] | not null default `'{}'` |
| `computed_at` | timestamptz | not null |

## 📣 Notifications

### `notification_preferences`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `organization_id` | uuid | fk → `organizations.id` |
| `subject_type` | text | enum (`participant`,`team`,`admin`) |
| `subject_id` | uuid | not null |
| `triggers` | jsonb | not null default `'[]'` |
| `channels` | jsonb | not null default `'[]'` |
| `muted_until` | timestamptz | nullable |
| `created_at` / `updated_at` | timestamptz | not null |

### `notification_deliveries`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `trigger` | text | not null |
| `recipient_subject_type` | text | enum (`participant`,`team`,`admin`) |
| `recipient_subject_id` | uuid | not null |
| `channel` | text | enum (`email`,`discord_webhook`,`slack_webhook`,`sms`,`webhook`) |
| `address` | text | not null |
| `subject` | text | nullable |
| `body_text` / `body_html` | text | nullable |
| `metadata` | jsonb | not null default `'{}'` |
| `status` | text | enum (`queued`,`sent`,`failed`) |
| `failure_reason` | text | nullable |
| `retry_count` | int | not null default 0 |
| `organization_id` | uuid | fk → `organizations.id` |
| `created_at` / `sent_at` / `last_attempt_at` | timestamptz | nullable |

## 🧹 Maintenance

### `cleanup_policies`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `organization_id` | uuid | fk → `organizations.id` |
| `target` | text | enum (`stale_registrations`,`archived_events`,`logs`,`notifications`,`sessions`) |
| `run_every_hours` | int | not null |
| `retention_days` | int | not null |
| `enabled` | bool | not null default true |
| `last_run_at` | timestamptz | nullable |
| `meta` | jsonb | not null default `'{}'` |

### `archive_policies`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `organization_id` | uuid | fk |
| `apply_to_events_older_than_days` | int | not null |
| `mode` | text | enum (`soft_delete`,`move_to_cold_storage`,`export`) |
| `include_event_ids` / `exclude_event_ids` | uuid[] | not null default `'{}'` |
| `notify_contacts` | bool | not null default false |
| `enabled` | bool | not null default true |

### `migration_policies`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | uuid | pk |
| `name` | text | not null |
| `description` | text | nullable |
| `run_on_startup` | bool | not null default true |
| `retry_on_failure` | bool | not null default true |
| `max_retries` | int | not null default 3 |
| `last_run_at` | timestamptz | nullable |
| `last_status` | text | enum (`success`,`failure`) nullable |

## 🔐 Audit Tables (Future)

- `activity_log` (captures admin actions, season switches, manual score edits).
- `schema_migrations` (reserved for future migration tracking if needed).

## 🔗 Relationship Overview

- `organizations` → `seasons` → `events` → `stages` → `rounds` → `matches`.
- `participants` / `teams` ↔ `registrations` ↔ `events`.
- `matches` ↔ `match_games`; `matches` roll into `standings`.
- `notification_preferences` → `notification_deliveries`.
- Maintenance policies tie back to the singleton organization.
- `users` ↔ auth token tables (`email_verification_tokens`, `magic_link_tokens`, `sessions`) support login flows.

This schema is the baseline for implementation and can be evolved alongside the typed class definitions in `docs/classes/`.
