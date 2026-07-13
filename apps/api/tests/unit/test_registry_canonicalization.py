"""Unit tests for registry canonicalization and fingerprinting."""

from __future__ import annotations

from datetime import UTC, datetime

from app.registry.canonical import canonicalize_registry, compute_content_fingerprint
from app.registry.models import RegistryDocument


def _doc(*, payload: dict[str, object] | None = None) -> RegistryDocument:
    return RegistryDocument.model_validate(
        {
            "registry": {
                "id": "market-data-topics",
                "type": "topic",
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "owner": "platform",
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "dependencies": [],
                "metadata": {"b": 2, "a": 1},
            },
            "payload": payload if payload is not None else {"topics": ["events", "market-data"]},
        }
    )


def test_canonicalization_deterministic() -> None:
    left = canonicalize_registry(_doc())
    right = canonicalize_registry(_doc())
    assert left == right


def test_key_order_does_not_affect_fingerprint() -> None:
    a = RegistryDocument.model_validate(
        {
            "registry": {
                "id": "x",
                "type": "generic",
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "owner": "platform",
                "created_at": "2026-01-01T00:00:00Z",
                "dependencies": [],
                "metadata": {"b": 1, "a": 2},
            },
            "payload": {"z": 1, "y": 2},
        }
    )
    b = RegistryDocument.model_validate(
        {
            "registry": {
                "id": "x",
                "type": "generic",
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "owner": "platform",
                "created_at": "2026-01-01T00:00:00Z",
                "dependencies": [],
                "metadata": {"a": 2, "b": 1},
            },
            "payload": {"y": 2, "z": 1},
        }
    )
    assert compute_content_fingerprint(a) == compute_content_fingerprint(b)


def test_payload_change_affects_fingerprint() -> None:
    left = compute_content_fingerprint(_doc(payload={"topics": ["events"]}))
    right = compute_content_fingerprint(_doc(payload={"topics": ["audit"]}))
    assert left != right


def test_yaml_json_equivalent_same_fingerprint() -> None:
    # Same logical document constructed from equivalent mappings.
    yaml_like = _doc()
    json_like = RegistryDocument.model_validate(
        {
            "registry": {
                "id": "market-data-topics",
                "type": "topic",
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "owner": "platform",
                "created_at": "2026-01-01T00:00:00Z",
                "dependencies": [],
                "metadata": {"a": 1, "b": 2},
            },
            "payload": {"topics": ["events", "market-data"]},
        }
    )
    assert compute_content_fingerprint(yaml_like) == compute_content_fingerprint(json_like)
