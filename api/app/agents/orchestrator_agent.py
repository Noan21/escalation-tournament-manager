from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from api.app.agents.pairing_agent import PairingAgent
from api.app.agents.scoring_agent import ScoringAgent
from api.app.agents.season_agent import SeasonAgent
from api.app.models.events import Round
from api.app.schemas.orchestrator import OrchestratorAction, OrchestratorCommand, OrchestratorResult
from api.app.schemas.rounds import GenerateRoundRequest
from api.app.services.exceptions import ConflictError, ServiceError


class OrchestratorAgent:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pairing_agent = PairingAgent(session)
        self.scoring_agent = ScoringAgent(session)
        self.season_agent = SeasonAgent(session)

    async def run(self, event_id: UUID, command: OrchestratorCommand, *, actor_id: UUID) -> OrchestratorResult:
        if command.action == OrchestratorAction.GENERATE_ROUND:
            if not command.stage_id:
                raise ServiceError("stage_id required for generate_round")
            request = GenerateRoundRequest(round_number=command.round_number, pairing_seed=command.pairing_seed)
            try:
                round_profile = await self.pairing_agent.run(command.stage_id, request, actor_id=actor_id)
                return OrchestratorResult(message="round generated", round_id=round_profile.id)
            except ConflictError:
                result = await self.session.execute(
                    select(Round).where(Round.stage_id == command.stage_id).order_by(Round.number.desc())
                )
                existing = result.scalars().first()
                return OrchestratorResult(status="noop", message="round already exists", round_id=existing.id if existing else None)

        if command.action == OrchestratorAction.LOCK_ROUND:
            if not command.round_id:
                raise ServiceError("round_id required for lock_round")
            try:
                round_profile = await self.scoring_agent.lock_round(command.round_id, actor_id=actor_id)
                return OrchestratorResult(message="round locked", round_id=round_profile.id)
            except ConflictError:
                return OrchestratorResult(status="noop", message="round already locked", round_id=command.round_id)

        if command.action == OrchestratorAction.RECOMPUTE_SEASON:
            if not command.season_id:
                raise ServiceError("season_id required for recompute_season")
            leaderboard = await self.season_agent.recompute(command.season_id, actor_id=actor_id)
            return OrchestratorResult(message="season recomputed", season_id=leaderboard.season_id)

        raise ServiceError("Unsupported orchestrator action")


__all__ = ["OrchestratorAgent"]
