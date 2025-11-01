# Standings & Tiebreak

Typed structures for leaderboard snapshots and tiebreak auditing.

## 📊 Standings Rows

```python
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

SubjectType = Literal["participant", "team"]


class StandingsRow(BaseModel):
    id: UUID
    stage_id: UUID
    subject_type: SubjectType
    subject_id: UUID
    rank: int = Field(..., ge=1)
    match_points: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    byes: int = 0
    total_score: int = 0  # aggregate margin of victory
    strength_of_schedule: Optional[float] = None
    opponent_match_win_pct: Optional[float] = None
    head_to_head: Optional[Literal["ahead", "behind", "tied"]] = None
    breakers_applied: list[str] = Field(default_factory=list)
    updated_at: datetime

    def summary(self) -> dict[str, object]:
        return {
            "subject_type": self.subject_type,
            "subject_id": str(self.subject_id),
            "rank": self.rank,
            "match_points": self.match_points,
        }
```

- `breakers_applied` records the tiebreakers evaluated to reach the final rank.
- `summary()` delivers a small payload for UI quick views.

## 🧮 Tiebreak Snapshots

```python
class TiebreakSnapshot(BaseModel):
    standings_row_id: UUID
    breaker_key: str
    value: float
    order_applied: int = Field(..., ge=1)
    subject_ids: list[UUID] = Field(default_factory=list, description="All subjects tied at this breaker step.")
    computed_at: datetime
```

- Keep `order_applied` so we can replay the tiebreak sequence.
- `subject_ids` documents who was evaluated together for this breaker.

## 📈 Aggregated Standings

```python
class StandingsPayload(BaseModel):
    stage_id: UUID
    scoring_profile_key: str
    generated_at: datetime
    rows: list[StandingsRow] = Field(default_factory=list)
    tiebreak_snapshots: list[TiebreakSnapshot] = Field(default_factory=list)
```

- The `StandingAgent` can emit this payload to the API, ensuring the consumer sees rows + tiebreak audit trail.

## ✅ Implementation Notes

1. Persist these models in `app/models/standings.py`.
2. When the `StandingAgent` runs, populate `rows` ordered by rank and append snapshots for each breaker applied.
3. Provide API endpoints that return `StandingsPayload` so front-end tables can render consistent metadata.
