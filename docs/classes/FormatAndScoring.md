# Tournament & Scoring Classes

This document defines strongly typed configuration objects for tournament formats and scoring plugins. Logic is declarative, validated early, and resolved via type‑safe registries.

---

## 🧱 Core Building Blocks

```python
# classes.py
from typing import Literal, Optional, Sequence, Dict
from pydantic import BaseModel, Field, validator

# ---------- Tournament Formats ----------

class MissionRules(BaseModel):
    source: str = Field(..., description="Description of the mission pack/deck")
    unique_draws: bool = Field(False, description="If True, do not reuse a mission/rule once drawn")

class TeamRules(BaseModel):
    team_size: int = Field(1, ge=1)
    allows_teams: bool = Field(False)
    shared_command_points: bool = Field(False)
    nominate_single_warlord: bool = Field(False)
    require_same_super_faction: bool = Field(False, description="e.g., both Imperium or both Chaos or both Xenos")
    prohibit_duplicate_datasheets_across_team: bool = Field(False)
    prohibit_duplicate_epic_hero_across_team: bool = Field(False)
    single_instance_teamwide_army_rules: bool = Field(False, description="army rules with teamwide target chosen once")

class TournamentFormatConfig(BaseModel):
    """Base metadata shared by every tournament format plugin."""

    key: str = Field(..., description="Registry key used to resolve the format plugin.")
    name: str
    stage_type: Literal["swiss", "single_elim", "double_elim", "round_robin", "pods"]
    default_rounds: int = Field(ge=1, description="Fallback round count if none supplied.")
    min_players: int = Field(ge=2)
    max_players: Optional[int] = Field(default=None, ge=2)
    allows_teams: bool = False
    allows_draws: bool = True
    pairing_strategy_key: str = Field(..., description="Key for the registered PairingStrategy.")
    first_round_pairing: Literal["random", "seeded"] = "random"
    mission_rules: Optional[MissionRules] = None
    team_rules: Optional[TeamRules] = None

    @validator("max_players")
    def validate_max_players(cls, value, values):
        if value is not None and value < values["min_players"]:
            raise ValueError("max_players must be >= min_players")
        return value

class SwissFormatConfig(TournamentFormatConfig):
    """Detailed configuration for the Swiss format."""

    stage_type: Literal["swiss"] = "swiss"
    bye_points: int = Field(3, ge=0, description="Points awarded for a bye.")
    allow_repeats: bool = False
    top_cut_size: Optional[int] = Field(default=None, ge=2)

# ---------- Scoring ----------

class ResultPoints(BaseModel):
    win: int = Field(3, ge=0)
    draw: int = Field(1, ge=0)
    loss: int = Field(0, ge=0)
    bye: int = Field(3, ge=0)

class TiebreakerRule(BaseModel):
    metric: Literal[
        "opponent_match_win_pct",
        "head_to_head",
        "score_differential",
        "strength_of_schedule",
        "games_won",
        # Extended metrics for special events
        "favourite_game_votes",
        "favourite_army_votes",
        "game_scores",
    ]
    descending: bool = True

class ScoringProfile(BaseModel):
    key: str = Field(..., description="Registry key for the scoring plugin.")
    name: str
    default_points: ResultPoints = Field(default_factory=ResultPoints)
    allow_draws: bool = True
    allow_margin_of_victory: bool = True
    margin_cap: Optional[int] = Field(default=None, ge=0)
    standings_metrics: Sequence[TiebreakerRule] = (
        TiebreakerRule(metric="opponent_match_win_pct"),
        TiebreakerRule(metric="head_to_head"),
        TiebreakerRule(metric="score_differential"),
    )

class WeightedPodiumProfile(ScoringProfile):
    """For events where podium is a weighted blend of categories."""
    # e.g., 33/33/33 blend across gaming + soft scores
    gaming_weight: float = Field(1.0, ge=0)
    favourite_game_weight: float = Field(0.0, ge=0)
    favourite_army_weight: float = Field(0.0, ge=0)
    # caps and per-vote values for soft scores
    favourite_vote_points: int = Field(3, ge=0)
    max_favourite_game_points: int = Field(0, ge=0)
    max_favourite_army_points: int = Field(0, ge=0)
    # tiebreakers when weighted totals are equal
    weighted_tiebreakers: Sequence[TiebreakerRule] = (
        TiebreakerRule(metric="game_scores"),
        TiebreakerRule(metric="favourite_game_votes"),
        TiebreakerRule(metric="favourite_army_votes"),
    )

# ---------- Registries ----------

tournament_formats: Dict[str, TournamentFormatConfig] = {}
scoring_profiles: Dict[str, ScoringProfile] = {}
```

---

## 🎯 Built‑In: Standard Swiss + 3/1/0

```python
# registration.py
from classes import (
    SwissFormatConfig,
    MissionRules,
    TeamRules,
    ScoringProfile,
    TiebreakerRule,
    tournament_formats,
    scoring_profiles,
)

# Baseline Swiss
standard_swiss = SwissFormatConfig(
    key="swiss",
    name="Swiss (4 rounds)",
    default_rounds=4,
    min_players=8,
    allows_draws=True,
    pairing_strategy_key="swiss_pairing",
    bye_points=3,
    allow_repeats=False,
    top_cut_size=8,
)

tournament_formats[standard_swiss.key] = standard_swiss

scoring_profiles["standard_3_1_0"] = ScoringProfile(
    key="standard_3_1_0",
    name="Standard 3/1/0",
)
```

---

## 🛡️ Event Preset: Warhammer 40,000 **Throne of Skulls – Doubles**

Modeled from the published pack. Encodes teams of two, Swiss pairings, five rounds, 3/1/0 game points, soft‑score voting, and podium determined by a 33/33/33 blend of gaming + Favourite Game + Favourite Army. Missions come from the Chapter Approved 2025–26 deck and are not reused once drawn. First round is random; later rounds are Swiss.

```python
# tos_doubles.py
from classes import (
    SwissFormatConfig,
    MissionRules,
    TeamRules,
    WeightedPodiumProfile,
    TiebreakerRule,
    tournament_formats,
    scoring_profiles,
)

# Tournament format
throne_of_skulls_doubles = SwissFormatConfig(
    key="tos_doubles_2026",
    name="Throne of Skulls Doubles (5 rounds)",
    default_rounds=5,
    min_players=16,  # teams of two; adjust per event
    allows_draws=True,
    pairing_strategy_key="swiss_pairing",
    first_round_pairing="random",
    bye_points=3,
    allow_repeats=False,
    top_cut_size=None,  # no explicit top cut in pack
    mission_rules=MissionRules(
        source="Chapter Approved 2025–26 Mission Deck",
        unique_draws=True,
    ),
    team_rules=TeamRules(
        team_size=2,
        allows_teams=True,
        shared_command_points=True,
        nominate_single_warlord=True,
        require_same_super_faction=True,  # Imperium OR Chaos OR Xenos
        prohibit_duplicate_datasheets_across_team=True,
        prohibit_duplicate_epic_hero_across_team=True,
        single_instance_teamwide_army_rules=True,  # e.g., one Oath of Moment target per team
    ),
)

tournament_formats[throne_of_skulls_doubles.key] = throne_of_skulls_doubles

# Scoring profile
throne_of_skulls_scoring = WeightedPodiumProfile(
    key="tos_doubles_weighted",
    name="ToS Doubles 33/33/33",
    default_points=dict(win=3, draw=1, loss=0, bye=3),
    allow_draws=True,
    allow_margin_of_victory=False,   # pack does not use MOV for podium
    margin_cap=None,
    # Weighted podium calculation: equal thirds
    gaming_weight=1.0,
    favourite_game_weight=1.0,
    favourite_army_weight=1.0,
    favourite_vote_points=3,                 # each vote worth 3
    max_favourite_game_points=15,            # up to 5 votes across a weekend → 15 pts
    max_favourite_army_points=15,            # up to 5 votes across a weekend → 15 pts
    standings_metrics=(                      # used for within‑gaming leaderboard
        TiebreakerRule(metric="opponent_match_win_pct"),
        TiebreakerRule(metric="head_to_head"),
    ),
    weighted_tiebreakers=(                   # pack order: game scores, fav game votes, fav army votes
        TiebreakerRule(metric="game_scores"),
        TiebreakerRule(metric="favourite_game_votes"),
        TiebreakerRule(metric="favourite_army_votes"),
    ),
)

scoring_profiles[throne_of_skulls_scoring.key] = throne_of_skulls_scoring
```

### Notes encoded from event pack

* **Swiss pairing** after a **random round 1**.
* **Five rounds** over two days.
* **Teams of two**. Both armies must be from the **same super‑faction** (Imperium, Chaos, or Xenos). Identical datasheets and EPIC HERO are **not** duplicated across the team. Army rules with single‑target selection are chosen **once** for the team. Teams **share CP** and nominate **one Warlord**.
* **Game scoring** uses **3/1/0** (win/draw/loss). Soft‑score votes: **Favourite Game** and **Favourite Army**, each vote worth **3 points**, each category capped at **15** for podium blending.
* **Podium** determined by equal thirds: gaming score, Favourite Game votes, Favourite Army votes. **Tiebreakers** for final standings: game scores → Favourite Game votes → Favourite Army votes. Within the gaming leaderboard, use standard match OMW% → H2H.
* **Missions**: Chapter Approved 2025–26 deck with **no repeats** once drawn.

---

## 🗂 Registry Typing

```python
# access at runtime
from classes import tournament_formats, scoring_profiles

fmt = tournament_formats["tos_doubles_2026"]
score = scoring_profiles["tos_doubles_weighted"]
```

---

## ✅ Next Steps

1. Place these models in `app/plugins/formats.py` and `app/plugins/scoring.py`.
2. Expose registry factories with lazy loading so per‑event config can override defaults via environment or YAML.
3. Add validation tests:

   * Teams must meet super‑faction rule.
   * No duplicate datasheets or EPIC HERO across teammates.
   * Votes cannot exceed caps.
   * Mission draws respect uniqueness when configured.

```python
# tests/test_validation.py
# Write Pydantic .validate() unit tests for edge cases above.
```