"""Immutable Gap Scanner Foundation contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.market_data.events.bar import BarEvent
from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware
from app.premarket.gap.ordering import ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC
from app.premarket.gap.policy import (
    GAP_PERCENT_QUANTIZE_POLICY_ID,
    SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
)
from app.premarket.watchlist.models import Watchlist


class GapConfig(BaseModel):
    """Explicit gap scan configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    selection_policy_id: str = Field(
        default=SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
        min_length=1,
        max_length=128,
    )
    ordering_policy_id: str = Field(
        default=ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
        min_length=1,
        max_length=128,
    )
    gap_percent_quantize_policy_id: str = Field(
        default=GAP_PERCENT_QUANTIZE_POLICY_ID,
        min_length=1,
        max_length=128,
    )

    @field_validator("selection_policy_id")
    @classmethod
    def validate_selection_policy(cls, value: str) -> str:
        text = value.strip()
        if text != SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1:
            msg = f"unsupported selection_policy_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("ordering_policy_id")
    @classmethod
    def validate_ordering_policy(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC:
            msg = f"unsupported ordering_policy_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("gap_percent_quantize_policy_id")
    @classmethod
    def validate_quantize_policy(cls, value: str) -> str:
        text = value.strip()
        if text != GAP_PERCENT_QUANTIZE_POLICY_ID:
            msg = f"unsupported gap_percent_quantize_policy_id: {text}"
            raise ValueError(msg)
        return text


class GapScanRequest(BaseModel):
    """Immutable gap scan input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watchlist: Watchlist
    bars: tuple[BarEvent, ...]
    as_of: datetime
    config: GapConfig

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class GapRecord(BaseModel):
    """One deterministic overnight gap observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gap_record_id: str = Field(min_length=64, max_length=64)
    instrument_key: str = Field(min_length=1, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)
    previous_session_close: Decimal
    current_session_open: Decimal
    gap_percent: Decimal
    gap_direction: str = Field(min_length=1, max_length=16)
    event_time: datetime
    known_at: datetime
    as_of: datetime
    selection_policy_id: str = Field(min_length=1, max_length=128)
    previous_bar_source_event_id: str | None = Field(default=None, max_length=256)
    current_bar_source_event_id: str | None = Field(default=None, max_length=256)

    @field_validator("gap_record_id")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "gap_record_id must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator(
        "previous_session_close",
        "current_session_open",
        "gap_percent",
        mode="before",
    )
    @classmethod
    def parse_decimals(cls, value: object, info: ValidationInfo) -> Decimal:
        return require_finite_decimal(value, field_name=str(info.field_name))  # type: ignore[arg-type]

    @field_validator("event_time", "known_at", "as_of")
    @classmethod
    def require_utc_timestamps(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="timestamp")


class GapProvenance(BaseModel):
    """Replay-relevant gap collection provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_fingerprint: str = Field(min_length=64, max_length=64)
    input_fingerprint: str = Field(min_length=64, max_length=64)
    ordering_policy_id: str = Field(min_length=1, max_length=128)
    selection_policy_id: str = Field(min_length=1, max_length=128)
    source_identifiers: tuple[str, ...] = ()

    @field_validator("config_fingerprint", "input_fingerprint")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class GapCollection(BaseModel):
    """Deterministic gap scan output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    records: tuple[GapRecord, ...]
    provenance: GapProvenance

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")
