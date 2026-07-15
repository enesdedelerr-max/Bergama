"""Immutable data-quality contracts (#310)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.quality import DataQualityFlags
from app.market_data.timing import require_utc_aware

_MAX_SAFE_METADATA = 16
_MAX_SAFE_METADATA_KEY = 64
_MAX_SAFE_METADATA_VALUE = 256
_SAFE_REASON_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")
_SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "apikey", "authorization")


class QualityRuleId(StrEnum):
    SCHEMA_REQUIRED_FIELD = "schema.required_field"
    SCHEMA_INVALID_DECIMAL = "schema.invalid_decimal"
    PIT_INVALID_ORDER = "pit.invalid_order"
    IDENTITY_KEY_MISMATCH = "identity.key_mismatch"
    IDENTITY_INVALID_SOURCE = "identity.invalid_source"
    FRESHNESS_EVENT_STALE = "freshness.event_stale"
    FRESHNESS_INGESTION_LAG = "freshness.ingestion_lag"
    FRESHNESS_KNOWN_TO_INGESTED_LAG = "freshness.known_to_ingested_lag"
    COMPLETENESS_MISSING_VALUE = "completeness.missing_value"
    COMPLETENESS_INCOMPLETE_FLAG = "completeness.incomplete_flag"
    VALUE_INVALID_OHLC = "value.invalid_ohlc"
    VALUE_CROSSED_QUOTE = "value.crossed_quote"
    VALUE_NEGATIVE_QUANTITY = "value.negative_quantity"
    VALUE_INVALID_PRICE = "value.invalid_price"
    DUPLICATION_DUPLICATE_OBSERVATION = "duplication.duplicate_observation"
    SOURCE_INVALID_PROVENANCE = "source.invalid_provenance"
    SOURCE_UNSAFE_METADATA = "source.unsafe_metadata"
    OPERATIONAL_PUBLISH_FAILED = "operational.publish_failed"
    OPERATIONAL_WRITER_FAILED = "operational.writer_failed"
    OPERATIONAL_CHECKPOINT_FAILED = "operational.checkpoint_failed"
    OPERATIONAL_ADMISSION_OVERFLOW = "operational.admission_overflow"


ALL_RULE_IDS: tuple[QualityRuleId, ...] = tuple(QualityRuleId)


class QualitySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QualityStatus(StrEnum):
    PASSED = "passed"
    DEGRADED = "degraded"
    FAILED = "failed"
    CRITICAL = "critical"


class QualityAction(StrEnum):
    ACCEPT = "accept"
    ACCEPT_DEGRADED = "accept_degraded"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    HALT_PIPELINE = "halt_pipeline"


class QualityOperationalOutcomeType(StrEnum):
    PUBLISH_FAILED = "publish_failed"
    WRITER_FAILED = "writer_failed"
    CHECKPOINT_FAILED = "checkpoint_failed"
    REPLAY_FAILED = "replay_failed"
    BACKFILL_FAILED = "backfill_failed"
    ADMISSION_OVERFLOW = "admission_overflow"


class QualityEvaluationContext(BaseModel):
    """Optional bounded context for deterministic rule evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_idempotency_key: str | None = Field(default=None, max_length=512)
    expected_deduplication_key: str | None = Field(default=None, max_length=512)
    duplicate_observed: bool = False
    operational_rule_id: QualityRuleId | None = None
    operational_reason_code: str | None = Field(default=None, max_length=96)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def validate_safe_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_operational_rule(self) -> Self:
        if self.operational_rule_id is not None and not self.operational_rule_id.value.startswith(
            "operational."
        ):
            msg = "operational_rule_id must be an operational rule"
            raise ValueError(msg)
        return self


class QualityRuleResult(BaseModel):
    """Result for one closed-registry quality rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: QualityRuleId
    passed: bool
    severity: QualitySeverity
    reason_code: str = Field(min_length=1, max_length=96)
    measured_value: str | None = Field(default=None, max_length=128)
    threshold: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("reason_code")
    @classmethod
    def validate_reason_code(cls, value: str) -> str:
        text = value.strip().lower()
        if not text or any(ch not in _SAFE_REASON_CHARS for ch in text):
            msg = "reason_code must be a bounded machine-readable token"
            raise ValueError(msg)
        return text

    @field_validator("safe_metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class QualityAssessment(BaseModel):
    """Payload-free deterministic quality evaluation summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=64, max_length=64)
    event_type: str = Field(min_length=1, max_length=64)
    instrument_key: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    evaluated_at: datetime
    overall_status: QualityStatus
    highest_severity: QualitySeverity
    recommended_action: QualityAction
    rule_results: tuple[QualityRuleResult, ...]
    existing_quality_flags: DataQualityFlags
    policy_fingerprint: str = Field(min_length=64, max_length=64)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("assessment_id", "policy_fingerprint")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint fields must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("evaluated_at")
    @classmethod
    def utc_evaluated_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="evaluated_at")

    @field_validator("safe_metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_results_order(self) -> Self:
        ordered = tuple(sorted(self.rule_results, key=lambda result: result.rule_id.value))
        if self.rule_results != ordered:
            msg = "rule_results must be sorted by rule_id"
            raise ValueError(msg)
        return self


def validate_safe_metadata(value: dict[str, str]) -> dict[str, str]:
    if len(value) > _MAX_SAFE_METADATA:
        msg = f"safe_metadata may contain at most {_MAX_SAFE_METADATA} entries"
        raise ValueError(msg)
    cleaned: dict[str, str] = {}
    for key, raw in value.items():
        k = str(key).strip()
        v = str(raw).strip()
        lowered = k.lower()
        if not k or len(k) > _MAX_SAFE_METADATA_KEY or len(v) > _MAX_SAFE_METADATA_VALUE:
            msg = "safe_metadata keys/values exceed allowed bounds"
            raise ValueError(msg)
        if any(token in lowered for token in _SENSITIVE_TOKENS):
            msg = f"forbidden safe_metadata key {k!r}"
            raise ValueError(msg)
        cleaned[k] = v
    return cleaned
