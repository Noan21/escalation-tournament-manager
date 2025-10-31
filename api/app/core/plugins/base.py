from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Match, Round, Stage


@dataclass(slots=True)
class PairingRequest:
    stage: Stage
    round_number: int


@dataclass(slots=True)
class MatchDescriptor:
    table_no: int
    side_a: dict[str, str | None]
    side_b: dict[str, str | None]
    meta: dict[str, object] | None = None


@dataclass(slots=True)
class ScoringContext:
    stage: Stage
    round: Round
    matches: Sequence[Match]


class PairingStrategy(ABC):
    key: str

    @abstractmethod
    async def generate(self, request: PairingRequest, session: AsyncSession) -> Iterable[MatchDescriptor]:
        """Produce match descriptors for a round."""


class ScoringStrategy(ABC):
    key: str

    @abstractmethod
    async def update_standings(self, context: ScoringContext, session: AsyncSession) -> None:
        """Apply scoring rules to standings for a given round."""


T_co = TypeVar("T_co", covariant=True)


class Registry(Protocol[T_co]):
    def register(self, strategy: T_co) -> None:
        ...

    def get(self, key: str) -> T_co:
        ...
