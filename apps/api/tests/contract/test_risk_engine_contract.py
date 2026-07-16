"""Contract tests for Risk Engine purity and boundaries (#403)."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

from app.risk import RULE_ORDER, RiskFinalAction, RiskRuleStatus
from app.risk.rules import RULE_ORDER as RULE_ORDER_DIRECT
from tests.support.risk_helpers import T0, empty_snapshot, engine, intent, policy

RISK_DIR = Path(__file__).resolve().parents[2] / "app" / "risk"


def test_rule_order_export_matches() -> None:
    assert RULE_ORDER == RULE_ORDER_DIRECT


def test_contract_approve_reject_halt_only() -> None:
    assert {action.value for action in RiskFinalAction} == {"APPROVE", "REJECT", "HALT"}
    assert {status.value for status in RiskRuleStatus} == {"PASS", "FAIL", "SKIPPED"}


def test_same_input_same_assessment_contract() -> None:
    risk = engine()
    kwargs = dict(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=5),
    )
    a = risk.evaluate(**kwargs)
    b = risk.evaluate(**kwargs)
    assert a.assessment_id == b.assessment_id
    assert a.assessment_hash == b.assessment_hash
    assert [r.rule_id for r in a.rule_results] == list(RULE_ORDER)


def test_risk_package_has_no_forbidden_side_effect_imports() -> None:
    forbidden = {
        "kafka",
        "aiokafka",
        "httpx",
        "requests",
        "aiohttp",
        "sqlalchemy",
        "asyncpg",
        "psycopg",
        "redis",
        "boto3",
        "botocore",
        "pathlib",
        "socket",
        "subprocess",
    }
    # pathlib used only in this test; risk package itself must not import IO/network stacks.
    for path in RISK_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    assert root not in forbidden, f"{path.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden, f"{path.name} imports from {node.module}"


def test_risk_package_does_not_import_broker_or_oms_modules() -> None:
    for path in RISK_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                assert not module.startswith("app.oms")
                assert not module.startswith("app.execution")
                assert not module.startswith("app.broker")
                assert "aiokafka" not in module
                assert "sqlalchemy" not in module
