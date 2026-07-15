"""Strategy Engine downstream ports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.strategy.models import StrategyDecision


class StrategyDecisionPort(Protocol):
    """Infrastructure-neutral decision sink. Not a broker/order boundary."""

    async def publish_decision(self, decision: StrategyDecision) -> None: ...


class InMemoryStrategyDecisionPort:
    """Test/local sink that records decisions without side effects."""

    def __init__(self) -> None:
        self._decisions: list[StrategyDecision] = []

    async def publish_decision(self, decision: StrategyDecision) -> None:
        self._decisions.append(decision)

    @property
    def decisions(self) -> Sequence[StrategyDecision]:
        return tuple(self._decisions)

    def clear(self) -> None:
        self._decisions.clear()
