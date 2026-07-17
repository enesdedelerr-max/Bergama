"""Reference SDK strategy for contract validation."""

from __future__ import annotations

from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState


class SdkNoOpStrategy:
    """Contract-validation strategy that always emits NO_ACTION."""

    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, config
        action = StrategyAction.NO_ACTION
        decision_id = build_decision_id(
            strategy_id=context.strategy_id,
            strategy_version=context.strategy_version,
            strategy_instance_id=context.strategy_instance_id,
            run_id=context.run_id,
            execution_fingerprint_value=context.execution_fingerprint,
            action=action.value,
            runtime_protocol_version=context.runtime_protocol_version,
        )
        decision = StrategyDecision.from_execution(
            decision_id=decision_id,
            context=context,
            snapshot=feature_snapshot,
            action=action,
            confidence=0.0,
            reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
            processing_latency_ms=0.0,
            occurred_at=context.evaluation_time,
            decision_timestamp=context.evaluation_time,
        )
        next_state = None
        if previous_state is not None:
            step = int(previous_state.payload.get("step", "0"))
            next_state = NextStrategyState(
                state_schema_version=previous_state.state_schema_version,
                state_id=previous_state.state_id,
                strategy_id=context.strategy_id,
                strategy_instance_id=context.strategy_instance_id,
                payload={"step": str(step + 1)},
            )
        return StrategyExecutionOutput(decision=decision, next_state=next_state)
