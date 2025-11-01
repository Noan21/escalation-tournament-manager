from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AgentContext(Protocol):
    actor_id: str | None


@dataclass
class SimpleAgentContext:
    actor_id: str | None = None


__all__ = ["AgentContext", "SimpleAgentContext"]
