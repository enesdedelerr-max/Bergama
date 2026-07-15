"""Backfill request, slice, and run models (#309)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.backfill_settings import BackfillSettings
from app.market_data.backfill.errors import (
    BackfillInvalidRequestError,
    BackfillUnboundedRequestError,
    BackfillUnsupportedProviderError,
    BackfillUnsupportedSourceError,
)
from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware

BackfillSinkType = Literal["none", "publish_port"]
BackfillTerminalStatus = Literal[
    "completed",
    "failed",
    "cancelled",
    "completed_empty",
]
SliceStatus = Literal["pending", "running", "completed", "failed", "empty"]


class BackfillProvider(StrEnum):
    POLYGON = "polygon"
    FRED = "fred"
    BENZINGA = "benzinga"
    FINNHUB = "finnhub"
    SEC = "sec"


class BackfillSourceKind(StrEnum):
    AGGREGATES = "aggregates"
    OBSERVATIONS = "observations"
    NEWS = "news"
    PROFILE_REFRESH = "profile_refresh"
    FUNDAMENTALS_REFRESH = "fundamentals_refresh"
    BOTH_REFRESH = "both_refresh"
    RECENT_FILINGS = "recent_filings"
    # Explicitly rejected kinds:
    REALTIME = "realtime"
    ARCHIVES = "archives"


class BackfillCapability(StrEnum):
    HISTORICAL_BACKFILL = "historical_backfill"
    BOUNDED_REFRESH = "bounded_refresh"
    UNSUPPORTED = "unsupported"


class BackfillMode(StrEnum):
    DRY_RUN = "dry_run"
    VALIDATE_ONLY = "validate_only"
    PUBLISH = "publish"


class BackfillDecision(StrEnum):
    DRY_RUN_VALIDATED = "DRY_RUN_VALIDATED"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    REJECTED_VALIDATION = "REJECTED_VALIDATION"
    REJECTED_PIT = "REJECTED_PIT"
    SINK_FAILED = "SINK_FAILED"
    CANCELLED = "CANCELLED"


_CAPABILITY: dict[tuple[BackfillProvider, BackfillSourceKind], BackfillCapability] = {
    (
        BackfillProvider.POLYGON,
        BackfillSourceKind.AGGREGATES,
    ): BackfillCapability.HISTORICAL_BACKFILL,
    (
        BackfillProvider.FRED,
        BackfillSourceKind.OBSERVATIONS,
    ): BackfillCapability.HISTORICAL_BACKFILL,
    (
        BackfillProvider.BENZINGA,
        BackfillSourceKind.NEWS,
    ): BackfillCapability.HISTORICAL_BACKFILL,
    (
        BackfillProvider.FINNHUB,
        BackfillSourceKind.PROFILE_REFRESH,
    ): BackfillCapability.BOUNDED_REFRESH,
    (
        BackfillProvider.FINNHUB,
        BackfillSourceKind.FUNDAMENTALS_REFRESH,
    ): BackfillCapability.BOUNDED_REFRESH,
    (
        BackfillProvider.FINNHUB,
        BackfillSourceKind.BOTH_REFRESH,
    ): BackfillCapability.BOUNDED_REFRESH,
    (
        BackfillProvider.SEC,
        BackfillSourceKind.RECENT_FILINGS,
    ): BackfillCapability.BOUNDED_REFRESH,
}


def capability_for(
    provider: BackfillProvider,
    source_kind: BackfillSourceKind,
) -> BackfillCapability:
    if source_kind in {BackfillSourceKind.REALTIME, BackfillSourceKind.ARCHIVES}:
        return BackfillCapability.UNSUPPORTED
    return _CAPABILITY.get((provider, source_kind), BackfillCapability.UNSUPPORTED)


class PolygonSelector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ticker: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    currency: str = Field(min_length=3, max_length=3)
    venue: str | None = Field(default=None, max_length=32)
    multiplier: int = Field(default=1, ge=1, le=10_000)
    timespan: Literal["minute", "hour", "day"]
    adjusted: bool | None = None

    @field_validator("ticker", "currency")
    @classmethod
    def upper_required(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "value must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("venue")
    @classmethod
    def upper_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().upper()
        return text or None

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "instrument_key": self.instrument.instrument_key,
            "currency": self.currency,
            "venue": self.venue,
            "multiplier": self.multiplier,
            "timespan": self.timespan,
            "adjusted": self.adjusted,
        }


class FredSelector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fred_series_id: str = Field(min_length=1, max_length=64)
    series_id: str = Field(min_length=1, max_length=64)
    instrument: InstrumentId
    observation_start: str | None = Field(default=None, min_length=10, max_length=10)
    observation_end: str | None = Field(default=None, min_length=10, max_length=10)
    realtime_start: str | None = Field(default=None, min_length=10, max_length=10)
    realtime_end: str | None = Field(default=None, min_length=10, max_length=10)

    @field_validator("fred_series_id")
    @classmethod
    def upper_fred(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("series_id")
    @classmethod
    def strip_series(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "series_id must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator(
        "observation_start",
        "observation_end",
        "realtime_start",
        "realtime_end",
    )
    @classmethod
    def ymd(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if len(text) != 10 or text[4] != "-" or text[7] != "-":
            msg = "date bounds must be YYYY-MM-DD"
            raise ValueError(msg)
        return text

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "fred_series_id": self.fred_series_id,
            "series_id": self.series_id,
            "instrument_key": self.instrument.instrument_key,
            "observation_start": self.observation_start,
            "observation_end": self.observation_end,
            "realtime_start": self.realtime_start,
            "realtime_end": self.realtime_end,
        }


class BenzingaSelector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tickers: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()
    ticker_to_instrument: dict[str, InstrumentId] = Field(default_factory=dict)
    anchor_instrument: InstrumentId | None = None

    @field_validator("tickers", "channels", mode="before")
    @classmethod
    def coerce_tuple(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(value)
        return value

    def fingerprint_payload(self) -> dict[str, Any]:
        mapping = {
            str(k).strip().upper(): v.instrument_key
            for k, v in sorted(self.ticker_to_instrument.items(), key=lambda i: str(i[0]))
        }
        return {
            "tickers": sorted(t.strip().upper() for t in self.tickers),
            "channels": sorted(c.strip().lower() for c in self.channels),
            "ticker_to_instrument": mapping,
            "anchor_instrument_key": (
                self.anchor_instrument.instrument_key if self.anchor_instrument else None
            ),
        }


class FinnhubRefreshSelector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ticker: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    refresh_type: Literal["profile", "fundamentals", "both"]
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("ticker")
    @classmethod
    def upper_ticker(cls, value: str) -> str:
        return value.strip().upper()

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "instrument_key": self.instrument.instrument_key,
            "refresh_type": self.refresh_type,
            "currency": self.currency.strip().upper() if self.currency else None,
        }


class SecRefreshSelector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cik: str = Field(min_length=1, max_length=16)
    instrument: InstrumentId
    refresh_type: Literal["recent_filings"] = "recent_filings"
    max_filings: int | None = Field(default=None, ge=1, le=1000)

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "cik": self.cik.strip(),
            "instrument_key": self.instrument.instrument_key,
            "refresh_type": self.refresh_type,
            "max_filings": self.max_filings,
        }


class BackfillSlice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slice_id: str = Field(min_length=1, max_length=128)
    start_time: datetime
    end_time: datetime
    provider_cursor: dict[str, str] = Field(default_factory=dict)
    status: SliceStatus = "pending"
    processed_count: int = Field(default=0, ge=0)
    published_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)

    @field_validator("start_time", "end_time")
    @classmethod
    def utc_bounds(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="slice_time")

    def evolve(self, **changes: object) -> BackfillSlice:
        data = self.model_dump(mode="python")
        data.update(changes)
        return BackfillSlice.model_validate(data)


class BackfillRequest(BaseModel):
    """One provider + one source_kind. Typed selectors only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: BackfillProvider
    source_kind: BackfillSourceKind
    start_time: datetime
    end_time: datetime
    max_records: int = Field(ge=1, le=100_000)
    mode: BackfillMode = BackfillMode.DRY_RUN
    batch_size: int | None = Field(default=None, ge=1, le=10_000)
    max_in_flight_events: int | None = Field(default=None, ge=1, le=100)
    events_per_second: float | None = Field(default=None, gt=0, le=10_000.0)
    checkpoint_id: str | None = Field(default=None, min_length=1, max_length=128)
    resume: bool = False
    allow_completed_rerun: bool = False
    slice_policy: str = Field(default="calendar", min_length=1, max_length=64)

    polygon: PolygonSelector | None = None
    fred: FredSelector | None = None
    benzinga: BenzingaSelector | None = None
    finnhub: FinnhubRefreshSelector | None = None
    sec: SecRefreshSelector | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="backfill_time")

    @field_validator("checkpoint_id")
    @classmethod
    def strip_checkpoint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @model_validator(mode="after")
    def validate_combination(self) -> Self:
        if self.start_time >= self.end_time:
            msg = "start_time must be < end_time"
            raise ValueError(msg)
        capability = capability_for(self.provider, self.source_kind)
        if capability is BackfillCapability.UNSUPPORTED:
            msg = f"unsupported provider/source: {self.provider.value}/{self.source_kind.value}"
            raise ValueError(msg)
        selected = {
            BackfillProvider.POLYGON: self.polygon,
            BackfillProvider.FRED: self.fred,
            BackfillProvider.BENZINGA: self.benzinga,
            BackfillProvider.FINNHUB: self.finnhub,
            BackfillProvider.SEC: self.sec,
        }
        for provider, selector in selected.items():
            if provider is self.provider:
                if selector is None:
                    msg = f"{provider.value} selector is required"
                    raise ValueError(msg)
            elif selector is not None:
                msg = f"unexpected selector for provider {self.provider.value}"
                raise ValueError(msg)
        # Cross-check source_kind vs selector
        if (
            self.provider is BackfillProvider.POLYGON
            and self.source_kind is not BackfillSourceKind.AGGREGATES
        ):
            msg = "polygon supports source_kind=aggregates only"
            raise ValueError(msg)
        if (
            self.provider is BackfillProvider.FRED
            and self.source_kind is not BackfillSourceKind.OBSERVATIONS
        ):
            msg = "fred supports source_kind=observations only"
            raise ValueError(msg)
        if (
            self.provider is BackfillProvider.BENZINGA
            and self.source_kind is not BackfillSourceKind.NEWS
        ):
            msg = "benzinga supports source_kind=news only"
            raise ValueError(msg)
        if self.provider is BackfillProvider.FINNHUB and self.source_kind not in {
            BackfillSourceKind.PROFILE_REFRESH,
            BackfillSourceKind.FUNDAMENTALS_REFRESH,
            BackfillSourceKind.BOTH_REFRESH,
        }:
            msg = "finnhub supports refresh source_kinds only"
            raise ValueError(msg)
        if (
            self.provider is BackfillProvider.SEC
            and self.source_kind is not BackfillSourceKind.RECENT_FILINGS
        ):
            msg = "sec supports source_kind=recent_filings only"
            raise ValueError(msg)
        if self.finnhub is not None:
            expected = {
                "profile": BackfillSourceKind.PROFILE_REFRESH,
                "fundamentals": BackfillSourceKind.FUNDAMENTALS_REFRESH,
                "both": BackfillSourceKind.BOTH_REFRESH,
            }[self.finnhub.refresh_type]
            if self.source_kind is not expected:
                msg = "finnhub refresh_type must match source_kind"
                raise ValueError(msg)
        return self

    def capability(self) -> BackfillCapability:
        return capability_for(self.provider, self.source_kind)

    def selector_summary(self) -> dict[str, Any]:
        if self.polygon is not None:
            return self.polygon.fingerprint_payload()
        if self.fred is not None:
            return self.fred.fingerprint_payload()
        if self.benzinga is not None:
            return self.benzinga.fingerprint_payload()
        if self.finnhub is not None:
            return self.finnhub.fingerprint_payload()
        if self.sec is not None:
            return self.sec.fingerprint_payload()
        return {}

    def fingerprint(self, *, sink_type: BackfillSinkType) -> str:
        payload = {
            "provider": self.provider.value,
            "source_kind": self.source_kind.value,
            "selectors": self.selector_summary(),
            "start_time": self.start_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_time": self.end_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "mode": self.mode.value,
            "max_records": self.max_records,
            "batch_size": self.batch_size,
            "slice_policy": self.slice_policy,
            "sink_type": sink_type,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_backfill_request(request: BackfillRequest, settings: BackfillSettings) -> None:
    if request.max_records > settings.max_records:
        raise BackfillUnboundedRequestError(
            detail=f"max_records exceeds hard cap {settings.max_records}"
        )
    span = request.end_time - request.start_time
    if span > timedelta(days=settings.max_time_range_days):
        raise BackfillUnboundedRequestError(
            detail=f"time range exceeds max_time_range_days={settings.max_time_range_days}"
        )
    batch = request.batch_size if request.batch_size is not None else settings.default_batch_size
    if batch > settings.default_batch_size and batch > 10_000:
        raise BackfillInvalidRequestError(detail="batch_size exceeds allowed bound")
    capability = request.capability()
    if capability is BackfillCapability.UNSUPPORTED:
        if request.source_kind is BackfillSourceKind.REALTIME:
            raise BackfillUnsupportedProviderError(detail="polygon realtime is unsupported")
        if request.source_kind is BackfillSourceKind.ARCHIVES:
            raise BackfillUnsupportedSourceError(detail="sec archives are unsupported")
        raise BackfillUnsupportedSourceError(detail="unsupported provider/source")


class BackfillRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backfill_id: str
    provider: BackfillProvider
    source_kind: BackfillSourceKind
    mode: BackfillMode
    request_fingerprint: str
    sink_type: BackfillSinkType
    started_at: datetime
    completed_at: datetime
    slice_count: int
    processed_count: int
    published_count: int
    failed_count: int
    terminal_status: BackfillTerminalStatus


def new_backfill_id() -> str:
    return str(uuid4())
