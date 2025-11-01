from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.app.agents.orchestrator_agent import OrchestratorAgent
from api.app.dependencies.auth import require_roles
from api.app.dependencies.services import get_db_session
from api.app.schemas.orchestrator import OrchestratorCommand, OrchestratorResult
from api.app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


def _get_agent(session=Depends(get_db_session)) -> OrchestratorAgent:
    return OrchestratorAgent(session)


@router.post("/events/{event_id}/run", response_model=OrchestratorResult)
async def run_event_command(
    event_id: UUID,
    payload: OrchestratorCommand,
    agent: OrchestratorAgent = Depends(_get_agent),
    current_user=Depends(require_roles("admin")),
) -> OrchestratorResult:
    try:
        return await agent.run(event_id, payload, actor_id=current_user.id)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


__all__ = ["router"]
