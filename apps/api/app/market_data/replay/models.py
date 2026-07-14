"""Replay request, cursor, and run models (#308)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.replay_settings import ReplaySettings
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.replay.errors import (
    ReplayInvalidRequestError,
    ReplayUnboundedRequestError,
)
from app.market_data.timing import require_utc_aware

# Mirrors Iceberg approved routes — kept in application layer to avoid infra imports.
APPROVED_REPLAY_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "market.quote",
        "market.trade",
        "market.bar",
        "market.reference_data",
        "market.fundamental",
        "market.macro",
        "market.filing",
        "market.news",
    }
)

EVENT_TYPE_TO_TABLE: dict[str, str] = {
    "market.quote": "market_quotes",
    "market.trade": "market_trades",
    "market.bar": "market_bars",
    "market.reference_data": "market_reference_data",
    "market.fundamental": "market_fundamentals",
    "market.macro": "market_macro",
    "market.filing": "market_filings",
    "market.news": "market_news",
}

ReplaySourceType = Literal["iceberg"]
ReplaySinkType = Literal["none", "publish_port", "custom_sink"]
ReplayTerminalStatus = Literal[
    "completed",
    "failed",
    "cancelled",
    "completed_empty",
]


class ReplayMode(StrEnum):
    DRY_RUN = "dry_run"
    VALIDATE_ONLY = "validate_only"
    REPUBLISH = "republish"
    CUSTOM_SINK = "custom_sink"


class ReplayDecision(StrEnum):
    DRY_RUN_VALIDATED = "DRY_RUN_VALIDATED"
    VALIDATED = "VALIDATED"
    REPUBLISHED = "REPUBLISHED"
    CUSTOM_SINK_SUCCEEDED = "CUSTOM_SINK_SUCCEEDED"
    REJECTED_VALIDATION = "REJECTED_VALIDATION"
    REJECTED_PIT = "REJECTED_PIT"
    SINK_FAILED = "SINK_FAILED"
    CHECKPOINT_FAILED = "CHECKPOINT_FAILED"
    CANCELLED = "CANCELLED"


class ReplayCursor(BaseModel):
    """Deterministic resume cursor matching replay ordering key."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    occurred_at: datetime
    event_type: str = Field(min_length=1, max_length=128)
    instrument_key: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)

    @field_validator("occurred_at")
    @classmethod
    def utc_aware(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="occurred_at")

    @field_validator("event_type", "instrument_key", "idempotency_key")
    @classmethod
    def strip_required(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "cursor field must be non-empty"
            raise ValueError(msg)
        return text

    def as_tuple(self) -> tuple[datetime, str, str, str]:
        return (self.occurred_at, self.event_type, self.instrument_key, self.idempotency_key)


class ReplayRequest(BaseModel):
    """Bounded, typed replay selectors. No SQL / paths / arbitrary tables."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start_time: datetime
    end_time: datetime
    max_records: int = Field(ge=1, le=100_000)
    mode: ReplayMode = ReplayMode.DRY_RUN
    event_types: tuple[str, ...] = ()
    instrument_keys: tuple[str, ...] = ()
    source_providers: tuple[str, ...] = ()
    batch_size: int | None = Field(default=None, ge=1, le=10_000)
    max_in_flight: int | None = Field(default=None, ge=1, le=100)
    events_per_second: float | None = Field(default=None, gt=0, le=10_000.0)
    checkpoint_id: str | None = Field(default=None, min_length=1, max_length=128)
    resume: bool = False
    allow_completed_rerun: bool = False
    # Rejected when present via extra=forbid; reserved names documented for tests.
    # Callers must never pass table names / SQL / filesystem paths.

    @field_validator("start_time", "end_time")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="replay_time")

    @field_validator("event_types", "instrument_keys", "source_providers", mode="before")
    @classmethod
    def coerce_tuple(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(value)
        return value

    @field_validator("event_types")
    @classmethod
    def normalize_event_types(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        approved = APPROVED_REPLAY_EVENT_TYPES
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            text = str(raw).strip()
            if not text:
                msg = "event_types entries must be non-empty"
                raise ValueError(msg)
            if not text.startswith("market."):
                text = f"market.{text}"
            if text not in approved:
                msg = f"unsupported event_type selector: {text!r}"
                raise ValueError(msg)
            if text not in seen:
                seen.add(text)
                normalized.append(text)
        return tuple(sorted(normalized))

    @field_validator("instrument_keys", "source_providers")
    @classmethod
    def normalize_filters(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            text = str(raw).strip()
            if not text:
                msg = "filter entries must be non-empty"
                raise ValueError(msg)
            if text not in seen:
                seen.add(text)
                cleaned.append(text)
        return tuple(sorted(cleaned))

    @field_validator("checkpoint_id")
    @classmethod
    def strip_checkpoint_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.start_time >= self.end_time:
            msg = "start_time must be < end_time"
            raise ValueError(msg)
        return self

    def resolved_event_types(self) -> frozenset[str]:
        if self.event_types:
            return frozenset(self.event_types)
        return APPROVED_REPLAY_EVENT_TYPES

    def resolved_table_bases(self) -> tuple[str, ...]:
        """Derive tables from event_types only — never from caller table names."""
        return tuple(sorted({EVENT_TYPE_TO_TABLE[et] for et in self.resolved_event_types()}))

    def fingerprint(self, *, sink_type: ReplaySinkType) -> str:
        """Deterministic SHA-256 of stable request selectors (no secrets/runtime IDs)."""
        payload = {
            "source": "iceberg",
            "start_time": self.start_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_time": self.end_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "event_types": list(self.event_types),
            "instrument_keys": list(self.instrument_keys),
            "source_providers": list(self.source_providers),
            "max_records": self.max_records,
            "batch_size": self.batch_size,
            "mode": self.mode.value,
            "sink_type": sink_type,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_replay_request(request: ReplayRequest, settings: ReplaySettings) -> None:
    """Fail closed when request exceeds settings policy."""
    if request.max_records > settings.max_records:
        raise ReplayUnboundedRequestError(
            detail=f"max_records exceeds hard cap {settings.max_records}"
        )
    span = request.end_time - request.start_time
    max_span = timedelta(days=settings.max_time_range_days)
    if span > max_span:
        raise ReplayUnboundedRequestError(
            detail=f"time range exceeds max_time_range_days={settings.max_time_range_days}"
        )
    batch = request.batch_size if request.batch_size is not None else settings.default_batch_size
    if batch > settings.max_batch_size:
        raise ReplayInvalidRequestError(detail="batch_size exceeds max_batch_size")
    inflight = (
        request.max_in_flight
        if request.max_in_flight is not None
        else settings.default_max_in_flight
    )
    if inflight > settings.max_batch_size:
        raise ReplayInvalidRequestError(detail="max_in_flight exceeds allowed bound")
    if inflight > batch:
        raise ReplayInvalidRequestError(detail="max_in_flight must be <= batch_size")


class ReplayRecord(BaseModel):
    """One reconstructed canonical event prepared for replay ordering."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    occurred_at: datetime
    event_type: str
    instrument_key: str
    idempotency_key: str
    table_base: str
    event: CanonicalMarketEvent
    synthetic_symbol_effective_from: bool = False

    def cursor(self) -> ReplayCursor:
        return ReplayCursor(
            occurred_at=self.occurred_at,
            event_type=self.event_type,
            instrument_key=self.instrument_key,
            idempotency_key=self.idempotency_key,
        )

    def order_key(self) -> tuple[datetime, str, str, str]:
        return self.cursor().as_tuple()


class ReplayRunResult(BaseModel):
    """Terminal outcome of one replay run (no payloads)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    replay_id: str
    mode: ReplayMode
    request_fingerprint: str
    source: ReplaySourceType
    sink_type: ReplaySinkType
    started_at: datetime
    completed_at: datetime
    processed_count: int
    succeeded_count: int
    failed_count: int
    last_cursor: ReplayCursor | None
    terminal_status: ReplayTerminalStatus
    synthetic_reconstruction_count: int = 0


def new_replay_id() -> str:
    return str(uuid4())
