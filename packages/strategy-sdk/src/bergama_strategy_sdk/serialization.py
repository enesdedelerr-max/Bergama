"""Deterministic canonical serialization for SDK fingerprints."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import Enum
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize fingerprint-relevant data with stable ordering."""
    return json.dumps(
        _normalize(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _normalize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="python")
    if isinstance(value, dict):
        return {
            str(key): _normalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            msg = "NaN/Infinity are not allowed in fingerprint payloads"
            raise ValueError(msg)
        msg = "float values are not allowed in fingerprint payloads; use Decimal"
        raise TypeError(msg)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    msg = f"unsupported fingerprint payload type: {type(value).__name__}"
    raise TypeError(msg)
