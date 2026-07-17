"""Clean author-facing strategy package fixture for #406 boundary scans."""

from bergama_strategy_sdk import FeatureSnapshot, Strategy, StrategyExecutionOutput
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.state import PreviousStrategyState


class CleanAuthorStrategy:
    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        raise NotImplementedError("fixture only")


_: type[Strategy] = CleanAuthorStrategy
