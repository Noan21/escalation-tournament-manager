from __future__ import annotations

import asyncio
from uuid import UUID

import typer

from api.app.agents.orchestrator_agent import OrchestratorAgent
from api.app.core.database import async_session_factory
from api.app.schemas.orchestrator import OrchestratorAction, OrchestratorCommand


app = typer.Typer(help="Run orchestrator commands from the CLI")


async def _run_command(event_id: UUID, action: OrchestratorAction, stage_id: UUID | None, round_id: UUID | None, season_id: UUID | None) -> None:
    async with async_session_factory() as session:
        agent = OrchestratorAgent(session)
        command = OrchestratorCommand(action=action, stage_id=stage_id, round_id=round_id, season_id=season_id)
        result = await agent.run(event_id, command, actor_id=UUID(int=0))
        typer.echo(result.model_dump())


@app.command()
def run_event(
    event_id: UUID,
    action: OrchestratorAction,
    stage_id: UUID | None = typer.Option(None),
    round_id: UUID | None = typer.Option(None),
    season_id: UUID | None = typer.Option(None),
) -> None:
    asyncio.run(_run_command(event_id, action, stage_id, round_id, season_id))


if __name__ == "__main__":
    app()
