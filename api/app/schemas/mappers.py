from __future__ import annotations

from datetime import datetime

from api.app.models.events import CheckIn, Match, MatchGame, Registration, Round
from api.app.models.standings import Standing, TiebreakSnapshot as StandingSnapshot
from api.app.schemas.players import CheckInRecord, EventRegistration
from api.app.schemas.rounds import (
    GameResult,
    MatchAssignment,
    MatchProfile,
    MatchScore,
    ParticipantSlot,
    RoundProfile,
    RoundTiming,
)
from api.app.schemas.standings import StandingsPayload, StandingsRow, TiebreakSnapshot


def _round_timing(round_obj: Round) -> RoundTiming:
    return RoundTiming(
        pairings_released_at=round_obj.pairings_released_at,
        games_start_at=round_obj.games_start_at,
        submissions_due_at=round_obj.submissions_due_at,
        locked_at=round_obj.locked_at,
        published_at=round_obj.published_at,
    )


def to_round_profile(round_obj: Round) -> RoundProfile:
    return RoundProfile(
        id=round_obj.id,
        stage_id=round_obj.stage_id,
        number=round_obj.number,
        status=round_obj.status,
        timing=_round_timing(round_obj),
        pairing_seed=round_obj.pairing_seed,
        notes=round_obj.notes,
        created_at=round_obj.created_at,
        updated_at=round_obj.updated_at,
    )


def _to_game_result(game: MatchGame) -> GameResult:
    return GameResult(
        game_number=game.game_number,
        outcome=game.outcome,
        score_a=game.score_a,
        score_b=game.score_b,
        completed_at=game.completed_at,
        notes=game.notes,
    )


def _participant_slot_from_match(
    participant_id: str | None,
    team_id: str | None,
    seed: int | None,
) -> ParticipantSlot:
    return ParticipantSlot(
        participant_id=participant_id,
        team_id=team_id,
        seed=seed,
    )


def to_match_profile(match: Match) -> MatchProfile:
    return MatchProfile(
        id=match.id,
        round_id=match.round_id,
        state=match.state,
        pairing_order=match.pairing_order,
        assignment=MatchAssignment(
            table_number=match.table_number,
            judge_id=match.judge_id,
            stream_url=match.stream_url,
        ),
        slot_a=_participant_slot_from_match(
            match.slot_a_participant_id,
            match.slot_a_team_id,
            match.slot_a_seed,
        ),
        slot_b=_participant_slot_from_match(
            match.slot_b_participant_id,
            match.slot_b_team_id,
            match.slot_b_seed,
        ),
        games=[_to_game_result(game) for game in sorted(match.games, key=lambda g: g.game_number)],
        score=MatchScore(
            wins_a=match.wins_a,
            wins_b=match.wins_b,
            draws=match.draws,
            total_points_a=match.total_points_a,
            total_points_b=match.total_points_b,
        ),
        reported_by=match.reported_by,
        reported_at=match.reported_at,
        confirmed_by=match.confirmed_by,
        confirmed_at=match.confirmed_at,
        meta=match.meta or {},
    )


def to_event_registration(registration: Registration) -> EventRegistration:
    subject_id = registration.participant_id or registration.team_id
    return EventRegistration(
        id=registration.id,
        event_id=registration.event_id,
        subject_type=registration.subject_type,
        subject_id=subject_id,
        status=registration.status,
        seeding_score=float(registration.seeding_score) if registration.seeding_score else None,
        notes=registration.notes,
        registered_at=registration.registered_at,
        confirmed_at=registration.confirmed_at,
        checked_in_at=registration.checked_in_at,
        meta=registration.meta or {},
    )


def to_check_in_record(check_in: CheckIn) -> CheckInRecord:
    return CheckInRecord(
        registration_id=check_in.registration_id,
        recorded_by=check_in.recorded_by,
        method=check_in.method,
        recorded_at=check_in.recorded_at,
        note=check_in.note,
    )


def to_standings_row(standing: Standing) -> StandingsRow:
    return StandingsRow(
        id=standing.id,
        stage_id=standing.stage_id,
        subject_type=standing.subject_type,
        subject_id=standing.subject_id,
        rank=standing.rank,
        match_points=standing.match_points,
        wins=standing.wins,
        losses=standing.losses,
        draws=standing.draws,
        byes=standing.byes,
        total_score=standing.total_score,
        strength_of_schedule=float(standing.strength_of_schedule)
        if standing.strength_of_schedule is not None
        else None,
        opponent_match_win_pct=float(standing.opponent_match_win_pct)
        if standing.opponent_match_win_pct is not None
        else None,
        head_to_head=standing.head_to_head,
        breakers_applied=[str(b) for b in standing.breakers_applied or []],
        updated_at=standing.updated_at,
    )


def to_tiebreak_snapshot(snapshot: StandingSnapshot) -> TiebreakSnapshot:
    return TiebreakSnapshot(
        standings_row_id=snapshot.standings_id,
        breaker_key=snapshot.breaker_key,
        value=float(snapshot.value),
        order_applied=snapshot.order_applied,
        subject_ids=list(snapshot.subject_ids or []),
        computed_at=snapshot.computed_at,
    )


def build_standings_payload(
    stage_id: str,
    scoring_profile_key: str,
    generated_at: datetime,
    standings: list[Standing],
    snapshots: list[StandingSnapshot],
) -> StandingsPayload:
    rows = [to_standings_row(standing) for standing in standings]
    snapshot_rows = [to_tiebreak_snapshot(snapshot) for snapshot in snapshots]
    return StandingsPayload(
        stage_id=stage_id,
        scoring_profile_key=scoring_profile_key,
        generated_at=generated_at,
        rows=rows,
        tiebreak_snapshots=snapshot_rows,
    )


__all__ = [
    "build_standings_payload",
    "to_check_in_record",
    "to_event_registration",
    "to_match_profile",
    "to_round_profile",
    "to_standings_row",
    "to_tiebreak_snapshot",
]
