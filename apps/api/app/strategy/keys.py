"""Deterministic Strategy Engine key and serialization helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def canonical_strategy_json(value: Any) -> bytes:
    """Serialize replay-relevant strategy data with stable ordering."""
    return json.dumps(
        _normalize(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def strategy_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_strategy_json(value)).hexdigest()


def build_decision_id(
    *,
    strategy_id: str,
    strategy_version: str,
    strategy_instance_id: str,
    run_id: str,
    input_idempotency_key: str,
    configuration_fingerprint: str,
    action: str,
    evaluation_version: str,
) -> str:
    """Stable decision ID for the same strategy/input/config/action tuple."""
    return strategy_sha256(
        {
            "action": action,
            "configuration_fingerprint": configuration_fingerprint,
            "evaluation_version": evaluation_version,
            "input_idempotency_key": input_idempotency_key,
            "run_id": run_id,
            "strategy_id": strategy_id,
            "strategy_instance_id": strategy_instance_id,
            "strategy_version": strategy_version,
        }
    )


def _normalize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="python")
    if isinstance(value, dict):
        return {
            str(key): _normalize(item)
            for key, item in sorted(value.items(), key=lambda i: str(i[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        raise ValueError("NaN/Infinity are not allowed")
    return value
