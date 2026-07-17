"""Deprecation metadata — excluded from execution fingerprints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeprecationDescriptor(BaseModel):
    """Machine-readable deprecation metadata for public SDK symbols."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = Field(min_length=1, max_length=256)
    deprecated_since: str = Field(min_length=1, max_length=32)
    removal_not_before: str = Field(min_length=1, max_length=32)
    replacement: str = Field(min_length=1, max_length=256)
    migration_document: str = Field(min_length=1, max_length=2048)

    @field_validator("symbol", "replacement")
    @classmethod
    def strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "deprecation fields must be non-empty"
            raise ValueError(msg)
        return text


class MigrationGuidance(BaseModel):
    """Structured migration guidance for deprecated public APIs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    what_changed: str = Field(min_length=1, max_length=1024)
    why: str = Field(min_length=1, max_length=1024)
    replacement: str = Field(min_length=1, max_length=256)
    sdk_api_version_impact: str = Field(min_length=1, max_length=256)
    runtime_protocol_impact: str = Field(min_length=1, max_length=256)
    feature_schema_impact: str = Field(min_length=1, max_length=256)
    configuration_schema_impact: str = Field(min_length=1, max_length=256)
    fingerprint_impact: str = Field(min_length=1, max_length=256)
    fail_closed_behavior: str = Field(min_length=1, max_length=1024)
    rollback_path: str = Field(min_length=1, max_length=1024)
