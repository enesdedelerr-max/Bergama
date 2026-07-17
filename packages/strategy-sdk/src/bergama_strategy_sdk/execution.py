"""Strategy execution output and authoring protocol."""

from __future__ import annotations

from typing import Protocol

from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyDecision
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState
from pydantic import BaseModel, ConfigDict


class StrategyExecutionOutput(BaseModel):
    """Author-facing execution result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: StrategyDecision
    next_state: NextStrategyState | None = None


class Strategy(Protocol):
    """Infrastructure-neutral strategy contract for #406."""

    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput: ...
