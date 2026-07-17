"""Strategy SDK contract tests (#406)."""

from __future__ import annotations

import inspect

import bergama_strategy_sdk
from bergama_strategy_sdk.execution import Strategy


def test_public_sdk_root_exports_author_types_only() -> None:
    public = set(bergama_strategy_sdk.__all__)
    assert "Strategy" in public
    assert "FeatureSnapshot" in public
    assert "StrategyExecutionOutput" in public
    assert "StrategyEngine" not in public
    assert "StrategyBatchExecutionResult" not in dir(bergama_strategy_sdk)


def test_strategy_protocol_is_execute_only() -> None:
    params = inspect.signature(Strategy.execute).parameters
    assert "feature_snapshot" in params
    assert "context" in params
    assert "config" in params
    assert "previous_state" in params
