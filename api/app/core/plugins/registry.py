from collections.abc import Mapping
from typing import Generic, TypeVar

from app.core.plugins.base import PairingStrategy, ScoringStrategy


StrategyT = TypeVar("StrategyT", bound=PairingStrategy | ScoringStrategy)


class StrategyRegistry(Generic[StrategyT]):
    def __init__(self) -> None:
        self._store: dict[str, StrategyT] = {}

    def register(self, strategy: StrategyT) -> None:
        self._store[strategy.key] = strategy

    def get(self, key: str) -> StrategyT:
        try:
            return self._store[key]
        except KeyError as exc:  # pragma: no cover - simple guard
            raise KeyError(f"Strategy with key '{key}' is not registered") from exc

    @property
    def catalog(self) -> Mapping[str, StrategyT]:
        return self._store


pairing_registry: StrategyRegistry[PairingStrategy] = StrategyRegistry()
scoring_registry: StrategyRegistry[ScoringStrategy] = StrategyRegistry()
