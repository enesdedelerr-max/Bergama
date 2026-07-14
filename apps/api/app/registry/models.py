"""Immutable registry document and loaded provenance models."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_REGISTRY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_REGISTRY_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*))*)?"
    r"(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
)

# Documented examples only — validation accepts any matching type pattern.
KNOWN_REGISTRY_TYPES = frozenset(
    {
        "generic",
        "topic",
        "feature",
        "model",
        "prompt",
        "strategy",
        "dataset",
        "policy",
    }
)


def validate_semver(value: str) -> str:
    text = value.strip()
    if not _SEMVER_PATTERN.fullmatch(text):
        msg = f"invalid semantic version {value!r}"
        raise ValueError(msg)
    return text


def schema_major(schema_version: str) -> int:
    validated = validate_semver(schema_version)
    major_text, _, _ = validated.partition(".")
    return int(major_text)


class RegistryDependency(BaseModel):
    """Shallow dependency reference within a loaded registry set."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_id: str = Field(min_length=1)
    version_constraint: str = Field(default="*")
    required: bool = True

    @field_validator("registry_id")
    @classmethod
    def validate_registry_id(cls, value: str) -> str:
        text = value.strip()
        if not _REGISTRY_ID_PATTERN.fullmatch(text):
            msg = f"invalid registry_id {value!r}"
            raise ValueError(msg)
        return text

    @field_validator("version_constraint")
    @classmethod
    def validate_constraint(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "version_constraint must be non-empty"
            raise ValueError(msg)
        return text


class RegistryIdentity(BaseModel):
    """Registry metadata block (document.registry)."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    id: str = Field(min_length=1, alias="id")
    type: str = Field(min_length=1)
    version: str
    schema_version: str
    owner: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime | None = None
    description: str | None = None
    dependencies: tuple[RegistryDependency, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "registry id must be non-empty"
            raise ValueError(msg)
        if not _REGISTRY_ID_PATTERN.fullmatch(text):
            msg = f"invalid registry id {value!r}"
            raise ValueError(msg)
        return text

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        text = value.strip()
        if not _REGISTRY_TYPE_PATTERN.fullmatch(text):
            msg = f"invalid registry type {value!r}"
            raise ValueError(msg)
        return text

    @field_validator("owner")
    @classmethod
    def validate_owner(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "owner must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("version", "schema_version")
    @classmethod
    def validate_versions(cls, value: str) -> str:
        return validate_semver(value)

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            msg = "timestamps must be timezone-aware UTC"
            raise ValueError(msg)
        return value

    @field_validator("dependencies", mode="before")
    @classmethod
    def coerce_dependencies(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(value)
        return value

    @model_validator(mode="after")
    def reject_duplicate_dependencies(self) -> Self:
        seen: set[str] = set()
        for dep in self.dependencies:
            if dep.registry_id in seen:
                msg = f"duplicate dependency {dep.registry_id!r}"
                raise ValueError(msg)
            if dep.registry_id == self.id:
                msg = "self-dependency is not allowed"
                raise ValueError(msg)
            seen.add(dep.registry_id)
        return self


class RegistryDocument(BaseModel):
    """Root registry document contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry: RegistryIdentity
    payload: dict[str, Any]

    @property
    def registry_id(self) -> str:
        return self.registry.id


class LoadedRegistry(BaseModel):
    """Validated document plus load provenance (no raw parser objects)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document: RegistryDocument
    source_path: Path
    source_format: Literal["yaml", "json"]
    loaded_at: datetime
    content_fingerprint: str

    @property
    def registry_id(self) -> str:
        return self.document.registry_id


class RegistryLoadReport(BaseModel):
    """Result of a successful registry load."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registries: tuple[LoadedRegistry, ...]
    duration_ms: float
    schema_major: int


class RegistrySummary(BaseModel):
    """Safe operational summary — no payloads or paths."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    loaded: bool
    count: int
    required_count: int
    schema_major: int
    registry_ids: tuple[str, ...]
    aggregate_fingerprint: str | None
