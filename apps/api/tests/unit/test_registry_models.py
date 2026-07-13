"""Unit tests for registry document models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.registry.errors import (
    RegistrySchemaInvalidError,
    RegistrySelfDependencyError,
    RegistryUnsupportedSchemaVersionError,
)
from app.registry.models import RegistryDocument, validate_semver
from app.registry.validation import validate_document_mapping
from pydantic import ValidationError


def _base_registry(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "market-data-topics",
        "type": "topic",
        "version": "1.0.0",
        "schema_version": "1.0.0",
        "owner": "platform",
        "created_at": "2026-01-01T00:00:00Z",
        "dependencies": [],
        "metadata": {},
    }
    data.update(overrides)
    return {"registry": data, "payload": {"ok": True}}


def test_valid_document_parses() -> None:
    document = RegistryDocument.model_validate(_base_registry())
    assert document.registry_id == "market-data-topics"
    assert document.registry.created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_empty_registry_id_fails() -> None:
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(_base_registry(id=""))


def test_missing_owner_fails() -> None:
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(_base_registry(owner=""))


def test_invalid_semantic_version_fails() -> None:
    with pytest.raises(ValueError, match="invalid semantic version"):
        validate_semver("1.0")
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(_base_registry(version="not-a-version"))


def test_naive_timestamp_fails() -> None:
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(_base_registry(created_at="2026-01-01T00:00:00"))


def test_unknown_root_key_rejected() -> None:
    payload = _base_registry()
    payload["extra"] = True
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(payload)


def test_self_dependency_rejected() -> None:
    with pytest.raises(ValidationError, match="self-dependency"):
        RegistryDocument.model_validate(
            _base_registry(
                dependencies=[
                    {
                        "registry_id": "market-data-topics",
                        "version_constraint": "*",
                        "required": True,
                    }
                ]
            )
        )


def test_duplicate_dependencies_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate dependency"):
        RegistryDocument.model_validate(
            _base_registry(
                dependencies=[
                    {
                        "registry_id": "canonical-market-schema",
                        "version_constraint": "1.0.0",
                        "required": True,
                    },
                    {
                        "registry_id": "canonical-market-schema",
                        "version_constraint": "1.0.0",
                        "required": True,
                    },
                ]
            )
        )


def test_unsupported_schema_major_fails() -> None:
    with pytest.raises(RegistryUnsupportedSchemaVersionError):
        validate_document_mapping(
            _base_registry(schema_version="2.0.0"),
            supported_schema_major=1,
        )


def test_self_dependency_maps_to_typed_error() -> None:
    with pytest.raises((RegistrySelfDependencyError, RegistrySchemaInvalidError)):
        validate_document_mapping(
            _base_registry(
                dependencies=[
                    {
                        "registry_id": "market-data-topics",
                        "version_constraint": "*",
                        "required": True,
                    }
                ]
            ),
            supported_schema_major=1,
        )
