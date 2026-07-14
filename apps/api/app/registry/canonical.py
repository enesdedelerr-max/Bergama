"""Deterministic registry canonicalization and fingerprinting."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.registry.errors import RegistryFingerprintFailedError
from app.registry.models import RegistryDocument


def canonicalize_registry(document: RegistryDocument) -> bytes:
    """Return deterministic UTF-8 JSON bytes for fingerprinting.

    Uses the declared document only — no runtime provenance fields.
    """
    try:
        payload = document.model_dump(mode="python")
        _reject_unsupported(payload)
        return _dumps(_normalize(payload))
    except RegistryFingerprintFailedError:
        raise
    except Exception as exc:
        raise RegistryFingerprintFailedError("registry fingerprint failed") from exc


def compute_content_fingerprint(document: RegistryDocument) -> str:
    """SHA-256 hex digest over canonical registry bytes."""
    return hashlib.sha256(canonicalize_registry(document)).hexdigest()


def _dumps(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
            default=_json_default,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RegistryFingerprintFailedError("registry fingerprint failed") from exc


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise RegistryFingerprintFailedError("NaN/Infinity are not allowed")
        return value
    return value


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"unsupported type {type(value)!r}")


def _reject_unsupported(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsupported(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsupported(item)
        return
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise RegistryFingerprintFailedError("NaN/Infinity are not allowed")
    if isinstance(value, (bytes, bytearray, set, complex)):
        raise RegistryFingerprintFailedError("unsupported payload value")
