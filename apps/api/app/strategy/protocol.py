"""Strategy protocol boundary."""

from __future__ import annotations

from typing import Protocol

from app.strategy.context import StrategyContext
from app.strategy.models import StrategyDecision, StrategyInput


class Strategy(Protocol):
    """Infrastructure-neutral strategy contract."""

    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision: ...
