from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Iterable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.app.models.enums import MatchState, StandingSubjectType
from api.app.models.events import Match, Round, Stage
from api.app.models.standings import Standing, TiebreakSnapshot
from api.app.schemas.mappers import build_standings_payload
from api.app.schemas.standings import ComputeStandingsRequest, StandingsPayload
from api.app.services.exceptions import NotFoundError


class StandingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_stage(self, stage_id: UUID) -> Stage:
        result = await self.session.execute(
            select(Stage).options(joinedload(Stage.event)).where(Stage.id == stage_id)
        )
        stage = result.scalar_one_or_none()
        if not stage:
            raise NotFoundError("Stage not found")
        return stage

    async def compute_stage_standings(
        self,
        stage_id: UUID,
        *,
        scoring_profile_key: str | None,
        actor_id: UUID | None = None,
    ) -> StandingsPayload:
        stage = await self._load_stage(stage_id)
        scoring_key = scoring_profile_key or stage.scoring_key or stage.event.default_scoring_key

        round_ids_result = await self.session.execute(
            select(Round.id).where(Round.stage_id == stage_id)
        )
        round_ids = [row[0] for row in round_ids_result.all()]
        if not round_ids:
            await self.session.execute(delete(Standing).where(Standing.stage_id == stage_id))
            await self.session.commit()
            return build_standings_payload(stage_id, scoring_key, datetime.now(tz=UTC), [], [])

        matches_result = await self.session.execute(
            select(Match).where(
                Match.round_id.in_(round_ids),
                Match.state.in_([MatchState.COMPLETED, MatchState.BYE]),
            )
        )
        matches: Iterable[Match] = matches_result.scalars().all()

        totals: dict[UUID, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for match in matches:
            if match.slot_a_participant_id:
                totals[match.slot_a_participant_id]["events"] += 1
            if match.slot_b_participant_id:
                totals[match.slot_b_participant_id]["events"] += 1

            if match.state == MatchState.BYE:
                if match.slot_a_participant_id:
                    totals[match.slot_a_participant_id]["match_points"] += 3
                    totals[match.slot_a_participant_id]["wins"] += 1
                continue

            if match.slot_a_participant_id is None or match.slot_b_participant_id is None:
                continue

            if match.wins_a > match.wins_b:
                totals[match.slot_a_participant_id]["match_points"] += 3
                totals[match.slot_a_participant_id]["wins"] += 1
                totals[match.slot_b_participant_id]["losses"] += 1
            elif match.wins_b > match.wins_a:
                totals[match.slot_b_participant_id]["match_points"] += 3
                totals[match.slot_b_participant_id]["wins"] += 1
                totals[match.slot_a_participant_id]["losses"] += 1
            else:
                totals[match.slot_a_participant_id]["match_points"] += 1
                totals[match.slot_b_participant_id]["match_points"] += 1
                totals[match.slot_a_participant_id]["draws"] += 1
                totals[match.slot_b_participant_id]["draws"] += 1

            totals[match.slot_a_participant_id]["total_score"] += match.total_points_a or 0
            totals[match.slot_b_participant_id]["total_score"] += match.total_points_b or 0

        await self.session.execute(delete(Standing).where(Standing.stage_id == stage_id))

        sorted_subjects = sorted(
            totals.items(),
            key=lambda item: (-item[1]["match_points"], -item[1]["wins"], -item[1]["total_score"]),
        )

        for index, (subject_id, metrics) in enumerate(sorted_subjects, start=1):
            standing = Standing(
                stage_id=stage_id,
                subject_type=StandingSubjectType.PARTICIPANT,
                subject_id=subject_id,
                rank=index,
                match_points=metrics["match_points"],
                wins=metrics["wins"],
                losses=metrics["losses"],
                draws=metrics["draws"],
                total_score=metrics["total_score"],
                byes=0,
            )
            self.session.add(standing)

        await self.session.commit()

        standings_result = await self.session.execute(select(Standing).where(Standing.stage_id == stage_id))
        standings = standings_result.scalars().all()
        snapshot_result = await self.session.execute(
            select(TiebreakSnapshot).where(
                TiebreakSnapshot.standings_id.in_([standing.id for standing in standings])
            )
        )
        snapshots = snapshot_result.scalars().all()
        payload = build_standings_payload(
            stage_id=stage_id,
            scoring_profile_key=scoring_key,
            generated_at=datetime.now(tz=UTC),
            standings=standings,
            snapshots=snapshots,
        )
        return payload

    async def get_stage_standings(self, stage_id: UUID) -> StandingsPayload:
        stage = await self._load_stage(stage_id)
        standings_result = await self.session.execute(select(Standing).where(Standing.stage_id == stage_id))
        standings = standings_result.scalars().all()
        snapshot_result = await self.session.execute(
            select(TiebreakSnapshot).where(TiebreakSnapshot.standings_id.in_([standing.id for standing in standings]))
        )
        snapshots = snapshot_result.scalars().all()
        return build_standings_payload(
            stage_id=stage_id,
            scoring_profile_key=stage.scoring_key or stage.event.default_scoring_key,
            generated_at=datetime.now(tz=UTC),
            standings=standings,
            snapshots=snapshots,
        )

    async def publish_stage_standings(
        self,
        stage_id: UUID,
        *,
        actor_id: UUID,
    ) -> StandingsPayload:
        # In this initial implementation publishing is equivalent to recomputing.
        return await self.compute_stage_standings(stage_id, scoring_profile_key=None, actor_id=actor_id)


__all__ = ["StandingsService"]
