"""Strategy decision models — sole downstream strategy signal."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.features import FeatureSnapshot


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


class StrategyDecision(BaseModel):
    """Deterministic strategy output. Never a broker order or sized intent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=64, max_length=64)
    strategy_id: str = Field(min_length=1, max_length=128)
    strategy_version: str = Field(min_length=1, max_length=64)
    strategy_instance_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    instrument_key: str = Field(min_length=1, max_length=128)
    configuration_fingerprint: str = Field(min_length=64, max_length=64)
    execution_fingerprint: str = Field(min_length=64, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    occurred_at: datetime
    decision_timestamp: datetime
    action: StrategyAction
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: tuple[StrategyReasonCode, ...]
    processing_latency_ms: float = Field(ge=0.0)
    runtime_protocol_version: str = Field(min_length=1, max_length=32)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("decision_id", "configuration_fingerprint", "execution_fingerprint")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint fields must be sha256 hex"
            raise ValueError(msg)
        return text

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

    @classmethod
    def from_execution(
        cls,
        *,
        decision_id: str,
        context: StrategyExecutionContext,
        snapshot: FeatureSnapshot,
        action: StrategyAction,
        confidence: float,
        reason_codes: tuple[StrategyReasonCode, ...],
        processing_latency_ms: float,
        occurred_at: datetime,
        decision_timestamp: datetime,
        safe_metadata: dict[str, str] | None = None,
    ) -> StrategyDecision:
        return cls(
            decision_id=decision_id,
            strategy_id=context.strategy_id,
            strategy_version=context.strategy_version,
            strategy_instance_id=context.strategy_instance_id,
            run_id=context.run_id,
            instrument_key=snapshot.instrument_key,
            configuration_fingerprint=context.configuration_fingerprint,
            execution_fingerprint=context.execution_fingerprint,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            occurred_at=occurred_at,
            decision_timestamp=decision_timestamp,
            action=action,
            confidence=confidence,
            reason_codes=reason_codes,
            processing_latency_ms=processing_latency_ms,
            runtime_protocol_version=context.runtime_protocol_version,
            safe_metadata=safe_metadata or {},
        )
