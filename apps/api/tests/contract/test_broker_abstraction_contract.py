"""Contract tests for broker abstraction boundaries (#405)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.broker.capabilities import BrokerCapabilities
from app.broker.models import BrokerFillEvent, BrokerLifecycleEvent, BrokerSubmissionResult
from app.broker.outcomes import BrokerCommandOutcome
from app.orders.models import ExecutableOrder

BROKER_DIR = Path(__file__).resolve().parents[2] / "app" / "broker"


def test_paper_adapter_does_not_import_order_aggregate() -> None:
    text = (BROKER_DIR / "paper_adapter.py").read_text(encoding="utf-8")
    assert "OrderAggregate" not in text
    assert "PortfolioService" not in text
    assert "RiskEngine" not in text


def test_broker_package_forbids_side_effect_and_sdk_imports() -> None:
    forbidden = {
        "kafka",
        "aiokafka",
        "httpx",
        "requests",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "boto3",
        "alpaca",
        "ib_insync",
        "ibapi",
    }
    for path in BROKER_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                root = module.split(".", 1)[0]
                assert root not in forbidden, f"{path.name} imports {module}"
                assert not module.startswith("app.portfolio.service")
                assert not module.startswith("app.risk.engine")
                assert not module.startswith("app.strategy.engine")


def test_core_models_are_frozen() -> None:
    assert ExecutableOrder.model_config.get("frozen") is True
    assert BrokerCapabilities.model_config.get("frozen") is True
    assert BrokerSubmissionResult.model_config.get("frozen") is True
    assert BrokerLifecycleEvent.model_config.get("frozen") is True
    assert BrokerFillEvent.model_config.get("frozen") is True


def test_outcome_unknown_is_distinct() -> None:
    assert BrokerCommandOutcome.OUTCOME_UNKNOWN is not BrokerCommandOutcome.REJECTED
    assert BrokerCommandOutcome.OUTCOME_UNKNOWN is not BrokerCommandOutcome.FAILED_BEFORE_SEND
    assert BrokerCommandOutcome.OUTCOME_UNKNOWN is not BrokerCommandOutcome.ACKNOWLEDGED
