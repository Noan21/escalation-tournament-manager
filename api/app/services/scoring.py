from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.app.models.events import Match, Round
from api.app.models.enums import MatchState, RoundStatus
from api.app.schemas.mappers import to_match_profile, to_round_profile
from api.app.schemas.rounds import MatchProfile, MatchResultSubmit, ReopenRoundRequest, RoundProfile
from api.app.services.exceptions import ConflictError, NotFoundError
from api.app.services.standings import StandingsService


class ScoringService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_match(self, match_id: UUID) -> Match:
        result = await self.session.execute(
            select(Match)
            .where(Match.id == match_id)
            .options(joinedload(Match.games))
        )
        match = result.unique().scalar_one_or_none()
        if not match:
            raise NotFoundError("Match not found")
        return match

    async def _load_round(self, round_id: UUID) -> Round:
        result = await self.session.execute(
            select(Round)
            .where(Round.id == round_id)
            .options(joinedload(Round.matches).joinedload(Match.games))
        )
        round_obj = result.unique().scalar_one_or_none()
        if not round_obj:
            raise NotFoundError("Round not found")
        return round_obj

    async def submit_match_result(
        self,
        payload: MatchResultSubmit,
        *,
        actor_id: UUID,
    ) -> MatchProfile:
        match = await self._load_match(payload.match_id)
        match.wins_a = payload.wins_a
        match.wins_b = payload.wins_b
        match.draws = payload.draws
        match.total_points_a = payload.total_points_a or payload.wins_a * 3
        match.total_points_b = payload.total_points_b or payload.wins_b * 3
        match.reported_by = payload.reported_by
        match.reported_at = datetime.now(tz=UTC)
        match.confirmed_by = None
        match.confirmed_at = datetime.now(tz=UTC)
        match.state = MatchState.COMPLETED if match.wins_a != match.wins_b else MatchState.COMPLETED
        await self.session.commit()
        refreshed = await self._load_match(match.id)
        return to_match_profile(refreshed)

    async def lock_round(
        self,
        round_id: UUID,
        *,
        actor_id: UUID,
    ) -> RoundProfile:
        round_obj = await self._load_round(round_id)
        if round_obj.status == RoundStatus.LOCKED:
            raise ConflictError("Round already locked")
        incomplete_matches = [match for match in round_obj.matches if match.state not in {MatchState.COMPLETED, MatchState.BYE}]
        if incomplete_matches:
            raise ConflictError("All matches must be completed before locking the round")

        round_obj.status = RoundStatus.LOCKED
        round_obj.locked_at = datetime.now(tz=UTC)
        await self.session.commit()

        standings_service = StandingsService(self.session)
        await standings_service.compute_stage_standings(round_obj.stage_id, scoring_profile_key=None, actor_id=actor_id)

        await self.session.refresh(round_obj)
        return to_round_profile(round_obj)

    async def reopen_round(
        self,
        round_id: UUID,
        request: ReopenRoundRequest,
        *,
        actor_id: UUID,
    ) -> RoundProfile:
        round_obj = await self._load_round(round_id)
        round_obj.status = RoundStatus.SCHEDULED
        round_obj.locked_at = None
        round_obj.notes = request.reason
        await self.session.commit()
        await self.session.refresh(round_obj)
        return to_round_profile(round_obj)


__all__ = ["ScoringService"]
