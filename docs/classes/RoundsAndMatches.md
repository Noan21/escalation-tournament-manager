# Rounds & Matches

Strongly typed models for the competitive flow: how rounds progress, how matches are recorded, and how game-level results roll up.

## 🔁 Round Models

```python
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

RoundStatus = Literal["scheduled", "pairing", "active", "locked", "published"]


class RoundTiming(BaseModel):
    pairings_released_at: Optional[datetime] = None
    games_start_at: Optional[datetime] = None
    submissions_due_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


class RoundProfile(BaseModel):
    id: UUID
    stage_id: UUID
    number: int = Field(..., ge=1)
    status: RoundStatus = "scheduled"
    timing: RoundTiming = Field(default_factory=RoundTiming)
    pairing_seed: Optional[str] = Field(
        default=None,
        description="Optional deterministic seed used by the pairing strategy."
    )
    notes: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime
    updated_at: datetime

    def is_locked(self) -> bool:
        return self.status in {"locked", "published"}
```

- `RoundTiming` keeps lifecycle timestamps grouped together.
- `pairing_seed` lets us reproduce pairings when auditing.

## ⚔️ Match Models

```python
MatchState = Literal["scheduled", "in_progress", "completed", "bye", "forfeit", "cancelled"]
GameOutcome = Literal["win_a", "win_b", "draw", "pending"]


class MatchAssignment(BaseModel):
    table_number: Optional[int] = Field(default=None, ge=1)
    judge_id: Optional[UUID] = None
    stream_url: Optional[str] = None


class ParticipantSlot(BaseModel):
    participant_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    seed: Optional[int] = None
    points_before_round: Optional[int] = None

    @property
    def subject_id(self) -> Optional[UUID]:
        return self.participant_id or self.team_id


class GameResult(BaseModel):
    game_number: int = Field(..., ge=1)
    outcome: GameOutcome = "pending"
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=256)
```

- `ParticipantSlot` supports both solo and team entries, matching how registrations work.
- `GameResult` allows best-of-N tracking with optional score details.

```python
class MatchScore(BaseModel):
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    total_points_a: int = 0  # e.g., margin of victory
    total_points_b: int = 0
```

```python
class MatchProfile(BaseModel):
    id: UUID
    round_id: UUID
    state: MatchState = "scheduled"
    pairing_order: int = Field(..., ge=1, description="Within-round ordering for display.")
    assignment: MatchAssignment = Field(default_factory=MatchAssignment)
    slot_a: ParticipantSlot = Field(default_factory=ParticipantSlot)
    slot_b: ParticipantSlot = Field(default_factory=ParticipantSlot)
    games: list[GameResult] = Field(default_factory=list)
    score: MatchScore = Field(default_factory=MatchScore)
    reported_by: Optional[UUID] = None
    reported_at: Optional[datetime] = None
    confirmed_by: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    meta: dict[str, object] = Field(default_factory=dict)

    def is_complete(self) -> bool:
        return self.state in {"completed", "bye", "forfeit", "cancelled"}
```

- `games` and `score` are separated so the scoring agent can recompute totals if custom rules apply.
- `reported_by` / `confirmed_by` support self-reporting with admin verification.

## 🧾 Match Submission Payloads

```python
class MatchResultSubmit(BaseModel):
    match_id: UUID
    reported_by: UUID
    wins_a: int = Field(ge=0)
    wins_b: int = Field(ge=0)
    draws: int = Field(ge=0)
    total_points_a: Optional[int] = Field(default=None, ge=0)
    total_points_b: Optional[int] = Field(default=None, ge=0)
    game_details: Optional[list[GameResult]] = None
    note: Optional[str] = Field(default=None, max_length=512)
```

- This payload feeds the `ScoringAgent` and ensures totals are non-negative.
- `game_details` can be omitted for formats that only care about match-level results.

## ✅ Implementation Notes

1. Persist round/match schemas near the ORM models (e.g., `app/models/rounds.py`).
2. `PairingAgent` should populate `pairing_order`, `slot_a`, `slot_b`, and optionally `assignment.table_number`.
3. `ScoringAgent` recalculates `MatchScore` from raw results and sets `state="completed"` before a round locks.
4. Provide API views that expose `RoundProfile` + `MatchProfile` for both admin and player dashboards.
