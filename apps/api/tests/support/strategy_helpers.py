"""Shared Strategy Engine test helpers."""

from __future__ import annotations

from app.core.clock import Clock, FixedClock
from app.market_data.data_quality import (
    QualityAction,
    QualityAssessment,
    QualitySeverity,
    QualityStatus,
)
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_idempotency_key
from app.strategy import (
    InMemoryStrategyDecisionPort,
    NoOpStrategy,
    NoOpStrategyConfig,
    StrategyEngine,
    StrategyIdentity,
    StrategyRegistry,
    build_strategy_engine,
)
from tests.support.market_data_fixtures import T0


def strategy_identity(**overrides: object) -> StrategyIdentity:
    data: dict[str, object] = {
        "strategy_id": "noop",
        "strategy_version": "1.0.0",
        "strategy_instance_id": "noop:aapl:primary",
        "evaluation_version": "1.0.0",
    }
    data.update(overrides)
    return StrategyIdentity.model_validate(data)


def strategy_engine(
    *,
    clock: Clock | None = None,
    port: InMemoryStrategyDecisionPort | None = None,
) -> tuple[StrategyEngine, InMemoryStrategyDecisionPort]:
    resolved_port = port if port is not None else InMemoryStrategyDecisionPort()
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: NoOpStrategy())
    return (
        build_strategy_engine(
            clock=clock if clock is not None else FixedClock(T0),
            registry=registry,
            decision_port=resolved_port,
        ),
        resolved_port,
    )


def noop_config(**overrides: object) -> NoOpStrategyConfig:
    data: dict[str, object] = {"config_version": "1.0.0", "safe_metadata": {"purpose": "test"}}
    data.update(overrides)
    return NoOpStrategyConfig.model_validate(data)


def quality_assessment(
    event: CanonicalMarketEvent,
    *,
    action: QualityAction = QualityAction.ACCEPT,
    status: QualityStatus = QualityStatus.PASSED,
    severity: QualitySeverity = QualitySeverity.INFO,
) -> QualityAssessment:
    return QualityAssessment(
        assessment_id="a" * 64,
        event_type=event.event_type.value,
        instrument_key=event.instrument.instrument_key,
        idempotency_key=build_idempotency_key(event),
        evaluated_at=T0,
        overall_status=status,
        highest_severity=severity,
        recommended_action=action,
        rule_results=(),
        existing_quality_flags=event.quality,
        policy_fingerprint="b" * 64,
    )
