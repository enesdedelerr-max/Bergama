"""Deterministic EventEnvelope JSON serialization."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.events.envelope import EventEnvelope
from app.events.errors import (
    EventDeserializationError,
    EventHashMismatchError,
    EventSchemaInvalidError,
    EventSerializationError,
)

_HASH_FIELDS = (
    "event_id",
    "event_type",
    "schema_version",
    "source_system",
    "occurred_at",
    "ingested_at",
    "correlation_id",
    "causation_id",
    "idempotency_key",
    "payload",
    "metadata",
)


def compute_content_hash(event: EventEnvelope) -> str:
    """SHA-256 over canonical JSON of envelope fields excluding content_hash."""
    canonical = _canonical_dict_for_hash(event)
    encoded = _dumps(canonical)
    return hashlib.sha256(encoded).hexdigest()


def serialize_event(event: EventEnvelope) -> bytes:
    """Serialize envelope to deterministic UTF-8 JSON bytes."""
    try:
        hashed = event.model_copy(update={"content_hash": compute_content_hash(event)})
        payload = hashed.model_dump(mode="python")
        _reject_unsupported(payload)
        return _dumps(_normalize(payload))
    except (EventSerializationError, EventSchemaInvalidError):
        raise
    except Exception as exc:
        raise EventSerializationError("event serialization failed") from exc


def deserialize_event(data: bytes) -> EventEnvelope:
    """Deserialize and validate envelope; verify content_hash when present."""
    try:
        raw = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EventDeserializationError("event deserialization failed") from exc
    if not isinstance(raw, dict):
        raise EventSchemaInvalidError("event payload must be a JSON object")
    try:
        event = EventEnvelope.model_validate(raw)
    except Exception as exc:
        raise EventSchemaInvalidError("event schema invalid") from exc
    if event.content_hash is not None:
        expected = compute_content_hash(event)
        if event.content_hash != expected:
            raise EventHashMismatchError("event content hash mismatch")
    return event


def _canonical_dict_for_hash(event: EventEnvelope) -> dict[str, Any]:
    data = event.model_dump(mode="python")
    return {key: _normalize(data[key]) for key in _HASH_FIELDS}


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
        raise EventSerializationError("event serialization failed") from exc


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise EventSerializationError("NaN/Infinity are not allowed")
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
        raise EventSerializationError("NaN/Infinity are not allowed")
    if isinstance(value, (bytes, bytearray, set, complex)):
        raise EventSerializationError("unsupported payload value")
