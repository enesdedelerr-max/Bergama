"""Reference strategies for contract validation only."""

from __future__ import annotations

from pydantic import ConfigDict

from app.strategy.config import StrategyConfig
from app.strategy.context import StrategyContext
from app.strategy.keys import build_decision_id
from app.strategy.models import (
    StrategyAction,
    StrategyDecision,
    StrategyInput,
    StrategyReasonCode,
)


class NoOpStrategyConfig(StrategyConfig):
    """Config for NoOpStrategy. It intentionally has no trading parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class NoOpStrategy:
    """Contract-validation strategy that always emits NO_ACTION."""

    def __init__(self, config: NoOpStrategyConfig | None = None) -> None:
        self.config = config if config is not None else NoOpStrategyConfig()

    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision:
        action = StrategyAction.NO_ACTION
        decision_timestamp = context.clock.now()
        decision_id = build_decision_id(
            strategy_id=context.identity.strategy_id,
            strategy_version=context.identity.strategy_version,
            strategy_instance_id=context.identity.strategy_instance_id,
            run_id=strategy_input.run_id,
            input_idempotency_key=strategy_input.idempotency_key,
            configuration_fingerprint=context.configuration_fingerprint,
            action=action.value,
            evaluation_version=context.identity.evaluation_version,
        )
        return StrategyDecision.from_identity(
            decision_id=decision_id,
            identity=context.identity,
            strategy_input=strategy_input,
            configuration_fingerprint=context.configuration_fingerprint,
            decision_timestamp=decision_timestamp,
            action=action,
            confidence=0.0,
            reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
            processing_latency_ms=0.0,
        )
