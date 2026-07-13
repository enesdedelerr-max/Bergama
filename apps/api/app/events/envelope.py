"""Canonical EventEnvelope contract (Issue #208A)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventEnvelope(BaseModel):
    """Versioned, transport-neutral event envelope."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    occurred_at: datetime
    ingested_at: datetime
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str = Field(min_length=1)
    payload: dict[str, Any]
    content_hash: str | None = None
    metadata: dict[str, str] | None = None

    @field_validator("occurred_at", "ingested_at")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "timestamps must be timezone-aware UTC"
            raise ValueError(msg)
        return value

    @field_validator("event_type", "schema_version", "source_system", "idempotency_key")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "value must be non-empty"
            raise ValueError(msg)
        return value.strip()

    @field_validator("payload")
    @classmethod
    def payload_must_be_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            msg = "payload must be a JSON object"
            raise ValueError(msg)
        return value
