from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MissionRules(BaseModel):
    source: str = Field(..., description="Description of the mission pack/deck")
    unique_draws: bool = Field(
        False, description="If True, do not reuse a mission/rule once drawn"
    )


class TeamRules(BaseModel):
    team_size: int = Field(1, ge=1)
    allows_teams: bool = Field(False)
    shared_command_points: bool = Field(False)
    nominate_single_warlord: bool = Field(False)
    require_same_super_faction: bool = Field(
        False, description="e.g., both Imperium or both Chaos or both Xenos"
    )
    prohibit_duplicate_datasheets_across_team: bool = Field(False)
    prohibit_duplicate_epic_hero_across_team: bool = Field(False)
    single_instance_teamwide_army_rules: bool = Field(
        False, description="army rules with teamwide target chosen once"
    )


class TournamentFormatConfig(BaseModel):
    """Base metadata shared by every tournament format plugin."""

    key: str = Field(..., description="Registry key used to resolve the format plugin.")
    name: str
    stage_type: Literal["swiss", "single_elim", "double_elim", "round_robin", "pods"]
    default_rounds: int = Field(ge=1, description="Fallback round count if none supplied.")
    min_players: int = Field(ge=2)
    max_players: int | None = Field(default=None, ge=2)
    allows_teams: bool = False
    allows_draws: bool = True
    pairing_strategy_key: str = Field(
        ..., description="Key for the registered PairingStrategy."
    )
    first_round_pairing: Literal["random", "seeded"] = "random"
    mission_rules: MissionRules | None = None
    team_rules: TeamRules | None = None

    @model_validator(mode="after")
    def validate_max_players(self) -> TournamentFormatConfig:
        if self.max_players is not None and self.max_players < self.min_players:
            raise ValueError("max_players must be >= min_players")
        return self


class SwissFormatConfig(TournamentFormatConfig):
    """Detailed configuration for the Swiss format."""

    stage_type: Literal["swiss"] = "swiss"
    bye_points: int = Field(3, ge=0, description="Points awarded for a bye.")
    allow_repeats: bool = False
    top_cut_size: int | None = Field(default=None, ge=2)


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
    margin_cap: int | None = Field(default=None, ge=0)
    standings_metrics: Sequence[TiebreakerRule] = (
        TiebreakerRule(metric="opponent_match_win_pct"),
        TiebreakerRule(metric="head_to_head"),
        TiebreakerRule(metric="score_differential"),
    )


class WeightedPodiumProfile(ScoringProfile):
    """For events where podium is a weighted blend of categories."""

    gaming_weight: float = Field(1.0, ge=0)
    favourite_game_weight: float = Field(0.0, ge=0)
    favourite_army_weight: float = Field(0.0, ge=0)
    favourite_vote_points: int = Field(3, ge=0)
    max_favourite_game_points: int = Field(0, ge=0)
    max_favourite_army_points: int = Field(0, ge=0)
    weighted_tiebreakers: Sequence[TiebreakerRule] = (
        TiebreakerRule(metric="game_scores"),
        TiebreakerRule(metric="favourite_game_votes"),
        TiebreakerRule(metric="favourite_army_votes"),
    )


tournament_formats: dict[str, TournamentFormatConfig] = {}
scoring_profiles: dict[str, ScoringProfile] = {}


__all__ = [
    "MissionRules",
    "ResultPoints",
    "ScoringProfile",
    "SwissFormatConfig",
    "TeamRules",
    "TiebreakerRule",
    "TournamentFormatConfig",
    "WeightedPodiumProfile",
    "scoring_profiles",
    "tournament_formats",
]

