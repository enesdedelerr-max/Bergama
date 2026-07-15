"""Strategy Engine Foundation contracts (#401)."""

from __future__ import annotations

import inspect

from app.strategy import (
    Strategy,
    StrategyAction,
    StrategyDecision,
    StrategyDecisionPort,
    StrategyInput,
    StrategyRegistry,
)
from app.strategy.state import StrategyState


def test_strategy_protocol_shape_is_input_context_to_decision() -> None:
    sig = inspect.signature(Strategy.evaluate)
    assert list(sig.parameters) == ["self", "strategy_input", "context"]
    assert sig.return_annotation == "StrategyDecision"


def test_downstream_port_is_decision_only_not_order_or_broker() -> None:
    sig = inspect.signature(StrategyDecisionPort.publish_decision)
    assert list(sig.parameters) == ["self", "decision"]
    assert sig.return_annotation == "None"
    assert "order" not in sig.parameters
    assert "broker" not in sig.parameters


def test_decision_model_has_audit_identity_but_no_execution_fields() -> None:
    fields = set(StrategyDecision.model_fields)
    assert {
        "decision_id",
        "strategy_id",
        "strategy_version",
        "strategy_instance_id",
        "run_id",
        "instrument_id",
        "configuration_fingerprint",
        "quality_summary",
        "action",
        "reason_codes",
    }.issubset(fields)
    forbidden = {
        "order_id",
        "broker_order_id",
        "quantity",
        "limit_price",
        "cash",
        "portfolio_id",
        "position",
        "pnl",
    }
    assert fields.isdisjoint(forbidden)


def test_strategy_input_accepts_canonical_event_and_quality_summary() -> None:
    fields = set(StrategyInput.model_fields)
    assert "event" in fields
    assert "quality_summary" in fields
    assert "idempotency_key" in fields
    assert "deduplication_key" in fields


def test_strategy_action_vocabulary_is_position_intent_not_order_verb() -> None:
    values = {action.value for action in StrategyAction}
    assert values == {
        "NO_ACTION",
        "ENTER_LONG",
        "EXIT_LONG",
        "ENTER_SHORT",
        "EXIT_SHORT",
        "FLATTEN",
    }
    assert values.isdisjoint({"BUY", "SELL", "ORDER", "CANCEL", "REPLACE"})


def test_state_protocol_is_optional_snapshot_restore_boundary() -> None:
    assert hasattr(StrategyState, "snapshot")
    assert hasattr(StrategyState, "restore")
    assert "persist" not in dir(StrategyState)
    assert "database" not in dir(StrategyState)


def test_registry_has_no_plugin_or_dynamic_import_api() -> None:
    public = {name for name in dir(StrategyRegistry) if not name.startswith("_")}
    assert {"register", "unregister", "create", "list_strategy_ids", "exists"}.issubset(public)
    assert public.isdisjoint({"load_module", "load_entry_points", "import_path", "discover"})
