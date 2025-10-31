# agents.md  
Tournament Platform – Agent Roles and Automation Plan

This file defines the logical “agents” or service responsibilities for the tournament system.  
Each agent represents a clear function or automation trigger in the stack.  
They are not AI models — just isolated, callable units within the FastAPI backend or external schedulers.

---

## 🎯 Overview

| Agent | Domain | Trigger | Description |
|--------|---------|----------|--------------|
| **OrchestratorAgent** | System / Workflow | Admin UI or CLI | Coordinates multi-stage events, calls specific format agents. |
| **PairingAgent** | Event Operations | `POST /stages/{id}/rounds` | Generates pairings for the next round based on the format plugin. |
| **ScoringAgent** | Event Operations | `POST /rounds/{id}/lock` | Calculates match points, applies scoring strategy, updates standings. |
| **StandingAgent** | Stats / Reports | After round lock | Aggregates standings across rounds or stages, updates tiebreakers. |
| **RegistrationAgent** | Player & Team Ops | On signup or event creation | Validates participants, seeds attendance records. |
| **SeasonAgent** | Year-long aggregation | Nightly or on demand | Recomputes cumulative standings across all events in a season. |
| **NotificationAgent** | Optional | After pairing / round lock | Sends messages (email, webhook, or Discord) for new pairings and results. |
| **MaintenanceAgent** | Infra Ops | Scheduled job | Cleans stale data, archives completed events, runs migrations if pending. |

---

## 🧩 Agent Interfaces

Each agent is just a Python module under `/api/app/agents` exposing a callable `run()` method  
or FastAPI background task. Example pattern:

```python
# agents/pairing_agent.py
from app.plugins import pairing_registry
from app.models import Round

def run(stage_id: str, round_number: int, session):
    strategy = pairing_registry.resolve_for_stage(stage_id, session)
    matches = strategy.generate_pairings(stage_id, round_number, session)
    session.bulk_insert_mappings(Round, matches)
    session.commit()
    return {"round": round_number, "matches_created": len(matches)}
