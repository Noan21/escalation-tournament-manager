from __future__ import annotations

import math
import random
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.app.models.events import Match, Round, Stage
from api.app.models.enums import MatchState, RegistrationStatus, RoundStatus
from api.app.models.events import Registration
from api.app.schemas.mappers import to_match_profile, to_round_profile
from api.app.schemas.players import EventRegistration
from api.app.schemas.rounds import (
    AssignTablesRequest,
    GenerateRoundRequest,
    MatchProfile,
    PairingPreview,
    RoundProfile,
)
from api.app.services.exceptions import ConflictError, NotFoundError


class PairingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_stage(self, stage_id: UUID) -> Stage:
        result = await self.session.execute(
            select(Stage)
            .options(joinedload(Stage.event), joinedload(Stage.rounds))
            .where(Stage.id == stage_id)
        )
        stage = result.unique().scalar_one_or_none()
        if not stage:
            raise NotFoundError("Stage not found")
        return stage

    async def _confirmed_registrations(self, event_id: UUID) -> list[Registration]:
        result = await self.session.execute(
            select(Registration)
            .where(
                Registration.event_id == event_id,
                Registration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]),
            )
            .order_by(Registration.seeding_score.desc().nullslast(), Registration.registered_at.asc())
        )
        return list(result.scalars().all())

    def _pairings_from_registrations(
        self,
        registrations: Sequence[Registration],
        seed: str | None,
    ) -> list[dict[str, object]]:
        participants = [reg.participant_id for reg in registrations if reg.participant_id]
        if seed:
            random.Random(seed).shuffle(participants)
        pairs = []
        for index in range(0, len(participants), 2):
            slot_a = participants[index]
            slot_b = participants[index + 1] if index + 1 < len(participants) else None
            pairs.append({"a": slot_a, "b": slot_b})
        return pairs

    async def generate_round_pairings(
        self,
        stage_id: UUID,
        request: GenerateRoundRequest,
        *,
        actor_id: UUID,
    ) -> RoundProfile:
        stage = await self._load_stage(stage_id)
        registrations = await self._confirmed_registrations(stage.event_id)
        if not registrations:
            raise ConflictError("No confirmed registrations available for pairings")

        result = await self.session.execute(
            select(func.max(Round.number)).where(Round.stage_id == stage_id)
        )
        current_max = result.scalar() or 0
        round_number = request.round_number or current_max + 1

        existing_round = await self.session.execute(
            select(Round).where(Round.stage_id == stage_id, Round.number == round_number)
        )
        if existing_round.scalar_one_or_none():
            raise ConflictError("Round already exists with that number")

        pairings = self._pairings_from_registrations(registrations, request.pairing_seed)
        now = datetime.now(tz=UTC)
        round_obj = Round(
            stage_id=stage_id,
            number=round_number,
            status=RoundStatus.PAIRING,
            pairing_seed=request.pairing_seed,
            pairings_released_at=now,
        )
        self.session.add(round_obj)
        await self.session.flush()

        matches: list[Match] = []
        for order, matchup in enumerate(pairings, start=1):
            match_state = MatchState.BYE if matchup["b"] is None else MatchState.SCHEDULED
            match = Match(
                round_id=round_obj.id,
                pairing_order=order,
                slot_a_participant_id=matchup["a"],
                slot_b_participant_id=matchup["b"],
                state=match_state,
            )
            if match_state == MatchState.BYE:
                match.wins_a = 1
                match.state = MatchState.BYE
            matches.append(match)
            self.session.add(match)

        await self.session.commit()
        await self.session.refresh(round_obj)
        return to_round_profile(round_obj)

    async def preview_pairings(
        self,
        stage_id: UUID,
        request: GenerateRoundRequest,
        *,
        actor_id: UUID,
    ) -> PairingPreview:
        stage = await self._load_stage(stage_id)
        registrations = await self._confirmed_registrations(stage.event_id)
        if not registrations:
            raise ConflictError("No confirmed registrations available for pairings")

        result = await self.session.execute(
            select(func.max(Round.number)).where(Round.stage_id == stage_id)
        )
        current_max = result.scalar() or 0
        round_number = request.round_number or current_max + 1
        pairings = self._pairings_from_registrations(registrations, request.pairing_seed)

        mock_matches: list[MatchProfile] = []
        for order, matchup in enumerate(pairings, start=1):
            mock_match = Match(
                round_id=UUID(int=0),
                pairing_order=order,
                slot_a_participant_id=matchup["a"],
                slot_b_participant_id=matchup["b"],
                state=MatchState.SCHEDULED if matchup["b"] else MatchState.BYE,
            )
            mock_match.id = UUID(int=order)
            mock_matches.append(to_match_profile(mock_match))

        return PairingPreview(stage_id=stage_id, round_number=round_number, matches=mock_matches)

    async def assign_tables(
        self,
        round_id: UUID,
        request: AssignTablesRequest,
        *,
        actor_id: UUID,
    ) -> RoundProfile:
        round_obj = await self.session.execute(
            select(Round)
            .where(Round.id == round_id)
            .options(joinedload(Round.matches).joinedload(Match.games))
        )
        round_instance = round_obj.unique().scalar_one_or_none()
        if not round_instance:
            raise NotFoundError("Round not found")

        table_map = {assignment.match_id: assignment.table_number for assignment in request.assignments}
        for match in round_instance.matches:
            if match.id in table_map:
                match.table_number = table_map[match.id]

        await self.session.commit()
        await self.session.refresh(round_instance)
        return to_round_profile(round_instance)


__all__ = ["PairingService"]
