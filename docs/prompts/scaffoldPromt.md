“Tournament Platform Scaffold — Multi-format, Year-long”

Build a minimal, extensible tournament platform that supports multiple event formats per month. Focus on clean scaffolding and plug-in strategies for pairing and scoring.

Stack

Frontend: Next.js 15 (App Router) + TypeScript + Tailwind.

API: FastAPI (Python 3.11) async.

Data: PostgreSQL 16, SQLAlchemy 2.x + Alembic.

Runtime: Docker Compose.

Tooling: pnpm, Ruff + Black, mypy strict, ESLint + Prettier, pytest.

CI: GitHub Actions for lint, type, test.

Core design goals

Formats are pluggable: Swiss, Round-Robin, Teams, Knockout, Pods.

Scoring is pluggable: Win/Draw/Loss, VP margin, 20-0 system, custom points.

Stages: Events can contain multiple stages, each with its own format and scoring.

Neutral domain: No game-specific rules in core.

Workflows = Python services invoked by API calls.

Domain model (PostgreSQL)

Keep generic. Use UUID PKs. Timestamps in UTC.

organizations(id, name)

seasons(id, organization_id, name, year, start_date, end_date)

participants(id, display_name, meta jsonb) -- players or captains

teams(id, name, meta jsonb) -- optional per event

team_members(team_id fk, participant_id fk, unique(team_id, participant_id))

events(id, season_id fk, name, start_date, end_date, status enum[draft,active,complete])

stages(id, event_id fk, name, stage_order int, -- e.g., “Group”, “Finals”
format_key text, scoring_key text, config jsonb) -- plugin keys + config

registrations(id, event_id fk, participant_id fk null, team_id fk null,
unique(event_id, participant_id), unique(event_id, team_id))

rounds(id, stage_id fk, number int, locked bool default false, unique(stage_id, number))

matches(id, round_id fk, table_no int, -- table/board number
side_a_participant_id fk null, side_b_participant_id fk null,
side_a_team_id fk null, side_b_team_id fk null,
state enum[scheduled,completed,bye,cancelled] default scheduled,
score_a int default 0, score_b int default 0, meta jsonb)

standings(id, stage_id fk, subject_type enum[participant,team],
subject_id uuid, match_points int default 0, tb1 int default 0, tb2 int default 0,
wins int default 0, draws int default 0, losses int default 0, total_score int default 0,
unique(stage_id, subject_type, subject_id))

Indexes on foreign keys and (stage_id, subject_type, match_points desc).

Plugin interfaces (Python)

Use strategy pattern with registries.

core/plugins/registry.py

pairing_registry: Dict[str, PairingStrategy]

scoring_registry: Dict[str, ScoringStrategy]

core/plugins/base.py