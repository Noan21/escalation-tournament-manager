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

