export interface EventRegistration {
  id: string;
  event_id: string;
  subject_type: "participant" | "team";
  subject_id: string;
  status: "pending" | "confirmed" | "checked_in" | "withdrawn";
  seeding_score?: number | null;
  registered_at: string;
  confirmed_at?: string | null;
  checked_in_at?: string | null;
}

export interface CheckInRecord {
  registration_id: string;
  recorded_by: string | null;
  method: string;
  recorded_at: string;
  note?: string | null;
}

export interface RoundProfile {
  id: string;
  stage_id: string;
  number: number;
  status: string;
  pairing_seed?: string | null;
}

export interface StandingsRow {
  subject_id: string;
  rank: number;
  match_points: number;
  wins: number;
  losses: number;
  draws: number;
}

export interface StandingsPayload {
  stage_id: string;
  scoring_profile_key: string;
  generated_at: string;
  rows: StandingsRow[];
}

export interface SeasonLeaderboardRow {
  subject_id: string;
  display_name: string;
  match_points: number;
  wins: number;
  losses: number;
  draws: number;
  events_played: number;
}

export interface SeasonLeaderboard {
  season_id: string;
  computed_at: string;
  scoring_profile_key: string;
  rows: SeasonLeaderboardRow[];
}

export interface EventProfile {
  id: string;
  name: string;
  slug: string;
  status: string;
  starts_at: string;
  ends_at: string;
}

export interface CreateRegistrationPayload {
  subject_type: "participant" | "team";
  participant_id?: string;
  team_id?: string;
}

export interface MatchResultPayload {
  match_id: string;
  reported_by: string;
  wins_a: number;
  wins_b: number;
  draws: number;
  total_points_a?: number;
  total_points_b?: number;
}

export type NotificationChannel =
  | "email"
  | "discord_webhook"
  | "slack_webhook"
  | "sms"
  | "webhook";

export type NotificationSubjectType = "participant" | "team" | "admin";

export type NotificationTrigger =
  | "registration_confirmed"
  | "round_pairings"
  | "round_locked"
  | "standings_published"
  | "season_leaderboard";

export interface NotificationChannelConfig {
  channel: NotificationChannel;
  address: string;
  enabled: boolean;
  rate_limit_per_hour?: number | null;
}

export interface NotificationPreference {
  id: string;
  organization_id: string;
  subject_type: NotificationSubjectType;
  subject_id: string;
  triggers: NotificationTrigger[];
  channels: NotificationChannelConfig[];
  muted_until: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferenceUpsert {
  id?: string | null;
  organization_id: string;
  subject_type: NotificationSubjectType;
  subject_id: string;
  triggers: NotificationTrigger[];
  channels: NotificationChannelConfig[];
  muted_until?: string | null;
}

export interface NotificationDispatchRequest {
  trigger: NotificationTrigger;
  organization_id?: string | null;
  stage_id?: string | null;
  round_id?: string | null;
  season_id?: string | null;
  recipient_subject_type?: NotificationSubjectType | null;
  recipient_subject_ids?: string[] | null;
  subject?: string | null;
  body_text?: string | null;
  body_html?: string | null;
  context?: Record<string, unknown>;
}

export interface NotificationMessagePayload {
  trigger: NotificationTrigger;
  recipient_subject_type: NotificationSubjectType;
  recipient_subject_id: string;
  channel: NotificationChannel;
  address: string;
  subject?: string | null;
  body_text?: string | null;
  body_html?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NotificationDelivery {
  id: string;
  message: NotificationMessagePayload;
  sent_at: string | null;
  status: "queued" | "sent" | "failed";
  failure_reason?: string | null;
  retry_count: number;
  last_attempt_at?: string | null;
}

export interface MaintenanceSummary {
  summary: string;
  items_processed: number;
  details: string[];
}

export interface CleanupTriggerRequest {
  targets?: string[];
  dry_run?: boolean;
}

export interface ArchiveTriggerRequest {
  policy_ids?: string[];
  dry_run?: boolean;
}

export interface MigrationTriggerRequest {
  policy_ids?: string[];
  dry_run?: boolean;
}
