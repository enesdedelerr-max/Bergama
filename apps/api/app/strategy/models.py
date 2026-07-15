"""Strategy Engine input, action, and decision models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.data_quality.models import QualityAction, QualityAssessment
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.quality import DataQualityFlags
from app.market_data.timing import require_utc_aware, validate_point_in_time_order
from app.strategy.identity import StrategyIdentity


class StrategyAction(StrEnum):
    NO_ACTION = "NO_ACTION"
    ENTER_LONG = "ENTER_LONG"
    EXIT_LONG = "EXIT_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_SHORT = "EXIT_SHORT"
    FLATTEN = "FLATTEN"


class StrategyReasonCode(StrEnum):
    NO_ACTION_REFERENCE = "no_action_reference"
    QUALITY_DEGRADED = "quality_degraded"
    UNSUPPORTED_EVENT = "unsupported_event"
    STATE_RESTORED = "state_restored"
    STRATEGY_ERROR = "strategy_error"


class QualitySummary(BaseModel):
    """Payload-free quality state visible to strategies and audits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    flags: DataQualityFlags
    assessment_id: str | None = Field(default=None, min_length=64, max_length=64)
    overall_status: str | None = Field(default=None, max_length=32)
    highest_severity: str | None = Field(default=None, max_length=32)
    recommended_action: QualityAction | None = None

    @classmethod
    def from_event_and_assessment(
        cls,
        event: CanonicalMarketEvent,
        assessment: QualityAssessment | None,
    ) -> QualitySummary:
        if assessment is None:
            return cls(flags=event.quality)
        return cls(
            flags=event.quality,
            assessment_id=assessment.assessment_id,
            overall_status=assessment.overall_status.value,
            highest_severity=assessment.highest_severity.value,
            recommended_action=assessment.recommended_action,
        )

    @property
    def is_degraded(self) -> bool:
        return self.recommended_action is QualityAction.ACCEPT_DEGRADED or any(
            (
                self.flags.is_late,
                self.flags.is_revision,
                self.flags.is_stale,
                self.flags.is_estimated,
                self.flags.is_incomplete,
            )
        )


class StrategyInput(BaseModel):
    """One canonical event plus replay-safe evaluation context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: CanonicalMarketEvent
    instrument_id: InstrumentId
    run_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    deduplication_key: str = Field(min_length=1, max_length=512)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    quality_summary: QualitySummary
    received_at: datetime

    @field_validator("received_at")
    @classmethod
    def utc_received_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="received_at")

    @model_validator(mode="after")
    def validate_event_identity_and_quality(self) -> Self:
        if self.instrument_id != self.event.instrument:
            msg = "StrategyInput.instrument_id must match event.instrument"
            raise ValueError(msg)
        if self.idempotency_key != build_idempotency_key(self.event):
            msg = "StrategyInput.idempotency_key mismatch"
            raise ValueError(msg)
        if self.deduplication_key != build_deduplication_key(self.event):
            msg = "StrategyInput.deduplication_key mismatch"
            raise ValueError(msg)
        if self.quality_summary.flags != self.event.quality:
            msg = "StrategyInput quality flags must match event quality"
            raise ValueError(msg)
        validate_point_in_time_order(
            occurred_at=self.event.occurred_at,
            effective_at=self.event.effective_at,
            known_at=self.event.known_at,
            ingested_at=self.event.ingested_at,
            quality=self.event.quality,
        )
        if self.quality_summary.recommended_action not in {
            None,
            QualityAction.ACCEPT,
            QualityAction.ACCEPT_DEGRADED,
        }:
            msg = "strategies may evaluate only accepted or accepted_degraded inputs"
            raise ValueError(msg)
        return self


class StrategyDecision(BaseModel):
    """Deterministic strategy output. Never a broker order."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=64, max_length=64)
    strategy_id: str = Field(min_length=1, max_length=128)
    strategy_version: str = Field(min_length=1, max_length=64)
    strategy_instance_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    instrument_id: InstrumentId
    configuration_fingerprint: str = Field(min_length=64, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    quality_summary: QualitySummary
    occurred_at: datetime
    decision_timestamp: datetime
    action: StrategyAction
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: tuple[StrategyReasonCode, ...]
    processing_latency_ms: float = Field(ge=0.0)
    evaluation_version: str = Field(min_length=1, max_length=32)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_identity(
        cls,
        *,
        decision_id: str,
        identity: StrategyIdentity,
        strategy_input: StrategyInput,
        configuration_fingerprint: str,
        decision_timestamp: datetime,
        action: StrategyAction,
        confidence: float,
        reason_codes: tuple[StrategyReasonCode, ...],
        processing_latency_ms: float,
        safe_metadata: dict[str, str] | None = None,
    ) -> StrategyDecision:
        return cls(
            decision_id=decision_id,
            strategy_id=identity.strategy_id,
            strategy_version=identity.strategy_version,
            strategy_instance_id=identity.strategy_instance_id,
            run_id=strategy_input.run_id,
            instrument_id=strategy_input.instrument_id,
            configuration_fingerprint=configuration_fingerprint,
            correlation_id=strategy_input.correlation_id,
            causation_id=strategy_input.causation_id,
            quality_summary=strategy_input.quality_summary,
            occurred_at=strategy_input.event.occurred_at,
            decision_timestamp=decision_timestamp,
            action=action,
            confidence=confidence,
            reason_codes=reason_codes,
            processing_latency_ms=processing_latency_ms,
            evaluation_version=identity.evaluation_version,
            safe_metadata=safe_metadata or {},
        )

    @field_validator("decision_id", "configuration_fingerprint")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint fields must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("occurred_at", "decision_timestamp")
    @classmethod
    def utc_timestamps(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="strategy_decision_timestamp")

    @field_validator("reason_codes")
    @classmethod
    def non_empty_reasons(
        cls, value: tuple[StrategyReasonCode, ...]
    ) -> tuple[StrategyReasonCode, ...]:
        if not value:
            msg = "StrategyDecision.reason_codes must be non-empty"
            raise ValueError(msg)
        return value

    @field_validator("safe_metadata")
    @classmethod
    def safe_metadata_only(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 16:
            msg = "safe_metadata may contain at most 16 entries"
            raise ValueError(msg)
        cleaned: dict[str, str] = {}
        for key, raw in value.items():
            k = str(key).strip()
            v = str(raw).strip()
            if not k or len(k) > 64 or len(v) > 256:
                msg = "safe_metadata keys/values exceed allowed bounds"
                raise ValueError(msg)
            if any(token in k.lower() for token in ("password", "secret", "token", "api_key")):
                msg = f"forbidden safe_metadata key {k!r}"
                raise ValueError(msg)
            cleaned[k] = v
        return cleaned
