"""Provider-independent data-quality rule engine tests (#310)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.clock import FixedClock
from app.market_data.data_quality import (
    DataQualityService,
    QualityEvaluationContext,
    QualityPolicy,
    QualityRuleId,
    QualitySeverity,
    default_quality_policy,
)
from app.market_data.enums import AdjustmentState, AssetClass, MarketEventType
from app.market_data.events.macro import MacroEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference
from tests.support.orchestrator_events import EVENT_TIME, trade_event


def _passing_policy() -> QualityPolicy:
    return QualityPolicy(
        freshness_thresholds_by_event_type={},
        max_ingestion_lag_by_event_type={},
        max_known_to_ingested_lag_by_event_type={},
    )


def test_valid_event_passes_without_threshold_policy() -> None:
    service = DataQualityService(policy=_passing_policy(), clock=FixedClock(EVENT_TIME))
    assessment = service.evaluate(trade_event())
    assert assessment.overall_status.value == "passed"
    assert assessment.recommended_action.value == "accept"
    assert all(result.passed for result in assessment.rule_results)


def test_incomplete_flag_is_observable_without_event_mutation() -> None:
    event = trade_event(quality=DataQualityFlags(is_incomplete=True))
    before = event.model_dump(mode="python")
    service = DataQualityService(policy=_passing_policy(), clock=FixedClock(EVENT_TIME))
    assessment = service.evaluate(event)
    assert assessment.overall_status.value == "degraded"
    assert assessment.recommended_action.value == "accept_degraded"
    assert event.model_dump(mode="python") == before
    assert any(
        result.rule_id is QualityRuleId.COMPLETENESS_INCOMPLETE_FLAG and not result.passed
        for result in assessment.rule_results
    )


def test_identity_key_mismatch_is_detected_from_context() -> None:
    service = DataQualityService(policy=_passing_policy(), clock=FixedClock(EVENT_TIME))
    assessment = service.evaluate(
        trade_event(),
        context=QualityEvaluationContext(expected_idempotency_key="wrong"),
    )
    assert assessment.overall_status.value == "failed"
    assert any(
        result.rule_id is QualityRuleId.IDENTITY_KEY_MISMATCH and not result.passed
        for result in assessment.rule_results
    )


def test_stale_trade_threshold_does_not_apply_to_macro_without_macro_policy() -> None:
    now = datetime(2024, 6, 15, tzinfo=UTC)
    policy = default_quality_policy(observe_only=True)
    service = DataQualityService(policy=policy, clock=FixedClock(now))
    assessment = service.evaluate(_macro_event())
    stale = next(
        result
        for result in assessment.rule_results
        if result.rule_id is QualityRuleId.FRESHNESS_EVENT_STALE
    )
    assert stale.passed is True
    assert stale.threshold is None
    assert stale.reason_code == "freshness_event_age_no_threshold"


def test_unsafe_metadata_can_be_detected_without_provider_branching() -> None:
    event = trade_event().model_copy(update={"metadata": {"api_key": "redacted"}})
    policy = _passing_policy().model_copy(
        update={
            "severity_overrides": {
                QualityRuleId.SOURCE_UNSAFE_METADATA: QualitySeverity.ERROR,
            },
            "observe_only": False,
            "reject_on_error": True,
        }
    )
    service = DataQualityService(policy=policy, clock=FixedClock(EVENT_TIME))
    assessment = service.evaluate(event)
    assert assessment.recommended_action.value == "reject"
    assert any(
        result.rule_id is QualityRuleId.SOURCE_UNSAFE_METADATA and not result.passed
        for result in assessment.rule_results
    )


def _macro_event() -> MacroEvent:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    instrument = InstrumentId(
        instrument_key="bergama:macro:fred:gdp",
        asset_class=AssetClass.MACRO,
        local_symbol="GDP",
        symbol_effective_from=ts,
    )
    return MacroEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument,
        source=SourceReference(
            provider="fred",
            source_symbol="GDP",
            source_event_id="GDP:2024-01-01",
        ),
        quality=DataQualityFlags(),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=ts,
        effective_at=ts,
        known_at=ts,
        ingested_at=ts,
        currency=None,
        venue=None,
        event_type=MarketEventType.MACRO,
        series_id="GDP",
        value="1",
    )
