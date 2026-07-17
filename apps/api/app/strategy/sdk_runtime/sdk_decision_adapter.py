"""Convert SDK decisions to legacy #401 decision port contracts."""

from __future__ import annotations

from bergama_strategy_sdk.decisions import StrategyAction as SdkStrategyAction
from bergama_strategy_sdk.decisions import StrategyDecision as SdkStrategyDecision
from bergama_strategy_sdk.decisions import StrategyReasonCode as SdkStrategyReasonCode
from bergama_strategy_sdk.errors import StrategyContractViolation

from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.strategy.models import QualitySummary, StrategyAction, StrategyDecision, StrategyReasonCode


def sdk_decision_to_legacy(
    decision: SdkStrategyDecision,
    *,
    instrument_id: InstrumentId,
    quality_summary: QualitySummary | None,
) -> StrategyDecision:
    """Map SDK decision to legacy DecisionPort shape.

    Requires a real host-supplied InstrumentId. Does not fabricate asset class,
    effective dates, or other identity fields.
    """
    if instrument_id.instrument_key != decision.instrument_key:
        raise StrategyContractViolation(
            detail=(
                f"instrument_key_mismatch:{instrument_id.instrument_key}!={decision.instrument_key}"
            )
        )
    resolved_quality = quality_summary or QualitySummary(flags=DataQualityFlags())
    return StrategyDecision(
        decision_id=decision.decision_id,
        strategy_id=decision.strategy_id,
        strategy_version=decision.strategy_version,
        strategy_instance_id=decision.strategy_instance_id,
        run_id=decision.run_id,
        instrument_id=instrument_id,
        configuration_fingerprint=decision.configuration_fingerprint,
        correlation_id=decision.correlation_id,
        causation_id=decision.causation_id,
        quality_summary=resolved_quality,
        occurred_at=decision.occurred_at,
        decision_timestamp=decision.decision_timestamp,
        action=StrategyAction(decision.action.value),
        confidence=decision.confidence,
        reason_codes=tuple(StrategyReasonCode(code.value) for code in decision.reason_codes),
        processing_latency_ms=decision.processing_latency_ms,
        evaluation_version=decision.runtime_protocol_version,
        safe_metadata=decision.safe_metadata,
    )


def sdk_action_to_legacy(action: SdkStrategyAction) -> StrategyAction:
    return StrategyAction(action.value)


def sdk_reason_to_legacy(code: SdkStrategyReasonCode) -> StrategyReasonCode:
    return StrategyReasonCode(code.value)
