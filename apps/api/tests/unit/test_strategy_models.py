"""Strategy Engine model and deterministic key tests (#401)."""

from __future__ import annotations

import pytest
from app.market_data.data_quality import QualityAction
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.strategy.config import StrategyConfig, strategy_config_fingerprint
from app.strategy.keys import build_decision_id
from app.strategy.models import (
    QualitySummary,
    StrategyAction,
    StrategyDecision,
    StrategyInput,
    StrategyReasonCode,
)
from pydantic import ValidationError
from tests.support.market_data_fixtures import T0, make_bar
from tests.support.strategy_helpers import quality_assessment, strategy_identity


def test_strategy_action_taxonomy_is_not_broker_order_language() -> None:
    assert {action.value for action in StrategyAction} == {
        "NO_ACTION",
        "ENTER_LONG",
        "EXIT_LONG",
        "ENTER_SHORT",
        "EXIT_SHORT",
        "FLATTEN",
    }
    assert "BUY" not in {action.value for action in StrategyAction}
    assert "ORDER" not in set(StrategyDecision.model_fields)


def test_config_is_strict_secret_free_and_deterministically_fingerprinted() -> None:
    config = StrategyConfig(config_version="1.0.0", safe_metadata={"purpose": "contract"})
    assert config.fingerprint() == strategy_config_fingerprint(config)
    assert (
        config.fingerprint()
        == StrategyConfig(
            safe_metadata={"purpose": "contract"},
            config_version="1.0.0",
        ).fingerprint()
    )

    with pytest.raises(ValidationError):
        StrategyConfig(config_version="1.0.0", arbitrary_code="x")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        StrategyConfig(safe_metadata={"api_key": "x"})
    with pytest.raises(ValueError, match="forbidden"):
        strategy_config_fingerprint({"nested": {"secret_token": "x"}})


def test_strategy_identity_uses_stable_tokens() -> None:
    identity = strategy_identity()
    assert identity.strategy_id == "noop"
    assert identity.strategy_instance_id == "noop:aapl:primary"
    with pytest.raises(ValidationError):
        strategy_identity(strategy_id="NoOp")


def test_strategy_input_validates_event_identity_keys_pit_and_quality() -> None:
    event = make_bar()
    assessment = quality_assessment(event)
    strategy_input = StrategyInput(
        event=event,
        instrument_id=event.instrument,
        run_id="run-1",
        session_id="session-1",
        idempotency_key=build_idempotency_key(event),
        deduplication_key=build_deduplication_key(event),
        quality_summary=QualitySummary.from_event_and_assessment(event, assessment),
        received_at=T0,
    )
    assert strategy_input.instrument_id == event.instrument
    assert strategy_input.quality_summary.recommended_action is QualityAction.ACCEPT

    with pytest.raises(ValidationError):
        StrategyInput(
            event=event,
            instrument_id=event.instrument,
            run_id="run-1",
            session_id="session-1",
            idempotency_key="wrong",
            deduplication_key=build_deduplication_key(event),
            quality_summary=QualitySummary.from_event_and_assessment(event, assessment),
            received_at=T0,
        )

    rejected = quality_assessment(event, action=QualityAction.REJECT)
    with pytest.raises(ValidationError):
        StrategyInput(
            event=event,
            instrument_id=event.instrument,
            run_id="run-1",
            session_id="session-1",
            idempotency_key=build_idempotency_key(event),
            deduplication_key=build_deduplication_key(event),
            quality_summary=QualitySummary.from_event_and_assessment(event, rejected),
            received_at=T0,
        )


def test_decision_id_builder_is_replay_safe_and_action_sensitive() -> None:
    common = {
        "strategy_id": "noop",
        "strategy_version": "1.0.0",
        "strategy_instance_id": "noop:aapl:primary",
        "run_id": "run-1",
        "input_idempotency_key": "input-1",
        "configuration_fingerprint": "c" * 64,
        "evaluation_version": "1.0.0",
    }
    first = build_decision_id(action=StrategyAction.NO_ACTION.value, **common)
    second = build_decision_id(action=StrategyAction.NO_ACTION.value, **common)
    changed = build_decision_id(action=StrategyAction.ENTER_LONG.value, **common)
    assert first == second
    assert first != changed
    assert len(first) == 64


def test_decision_rejects_empty_reason_and_sensitive_metadata() -> None:
    event = make_bar()
    identity = strategy_identity()
    config_hash = "c" * 64
    strategy_input = StrategyInput(
        event=event,
        instrument_id=event.instrument,
        run_id="run-1",
        session_id="session-1",
        idempotency_key=build_idempotency_key(event),
        deduplication_key=build_deduplication_key(event),
        quality_summary=QualitySummary.from_event_and_assessment(event, quality_assessment(event)),
        received_at=T0,
    )
    decision_id = build_decision_id(
        strategy_id=identity.strategy_id,
        strategy_version=identity.strategy_version,
        strategy_instance_id=identity.strategy_instance_id,
        run_id=strategy_input.run_id,
        input_idempotency_key=strategy_input.idempotency_key,
        configuration_fingerprint=config_hash,
        action=StrategyAction.NO_ACTION.value,
        evaluation_version=identity.evaluation_version,
    )
    with pytest.raises(ValidationError):
        StrategyDecision.from_identity(
            decision_id=decision_id,
            identity=identity,
            strategy_input=strategy_input,
            configuration_fingerprint=config_hash,
            decision_timestamp=T0,
            action=StrategyAction.NO_ACTION,
            confidence=0.0,
            reason_codes=(),
            processing_latency_ms=0.0,
        )
    with pytest.raises(ValidationError):
        StrategyDecision.from_identity(
            decision_id=decision_id,
            identity=identity,
            strategy_input=strategy_input,
            configuration_fingerprint=config_hash,
            decision_timestamp=T0,
            action=StrategyAction.NO_ACTION,
            confidence=0.0,
            reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
            processing_latency_ms=0.0,
            safe_metadata={"secret": "x"},
        )
