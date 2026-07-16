"""Contract tests for OMS boundaries (#404)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.orders import LEGAL_TRANSITIONS, OrderStatus
from app.orders.models import ExecutableOrder

ORDERS_DIR = Path(__file__).resolve().parents[2] / "app" / "orders"


def test_no_replace_statuses() -> None:
    assert "REPLACE_PENDING" not in OrderStatus.__members__
    assert "REPLACED" not in OrderStatus.__members__


def test_transition_matrix_covers_mvp_statuses() -> None:
    for status in OrderStatus:
        assert status in LEGAL_TRANSITIONS


def test_orders_package_has_no_forbidden_side_effect_imports() -> None:
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
        "socket",
        "subprocess",
    }
    for path in ORDERS_DIR.glob("*.py"):
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
                assert not module.startswith("app.broker")
                assert not module.startswith("app.execution")


def test_executable_order_is_frozen() -> None:
    assert ExecutableOrder.model_config.get("frozen") is True
