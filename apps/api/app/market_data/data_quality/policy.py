"""Data-quality policy models, action resolution and safe loading (#310)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from app.market_data.data_quality.errors import (
    DataQualityPolicyFileTooLargeError,
    DataQualityPolicyNotFoundError,
    DataQualityPolicyParseError,
    DataQualityPolicyPathError,
    DataQualityPolicySymlinkRejectedError,
)
from app.market_data.data_quality.models import (
    ALL_RULE_IDS,
    QualityAction,
    QualityRuleId,
    QualitySeverity,
    QualityStatus,
)
from app.market_data.enums import MarketEventType

_ALLOWED_EXTENSIONS = frozenset({".yaml", ".yml", ".json"})
_POLICY_SCHEMA_VERSION = "1.0.0"


class SustainedFailureThresholds(BaseModel):
    """Bounded thresholds for alert-ready aggregate signals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rejection_rate_percent: Decimal = Field(
        default=Decimal("25"),
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    stale_rate_percent: Decimal = Field(default=Decimal("25"), ge=Decimal("0"), le=Decimal("100"))
    minimum_events: int = Field(default=10, ge=1, le=1_000_000)


class QualityPolicy(BaseModel):
    """Strict, deterministic policy for event-quality assessment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version: str = Field(default=_POLICY_SCHEMA_VERSION, min_length=1, max_length=32)
    enabled_rules: tuple[QualityRuleId, ...] = Field(default_factory=lambda: ALL_RULE_IDS)
    disabled_rules: tuple[QualityRuleId, ...] = ()
    severity_overrides: dict[QualityRuleId, QualitySeverity] = Field(default_factory=dict)
    freshness_thresholds_by_event_type: dict[MarketEventType, int] = Field(default_factory=dict)
    max_ingestion_lag_by_event_type: dict[MarketEventType, int] = Field(default_factory=dict)
    max_known_to_ingested_lag_by_event_type: dict[MarketEventType, int] = Field(
        default_factory=dict
    )
    reject_on_error: bool = False
    halt_on_critical: bool = False
    quarantine_on_error: bool = False
    observe_only: bool = True
    aggregation_window_seconds: int = Field(default=300, ge=1, le=86_400)
    sustained_failure_thresholds: SustainedFailureThresholds = Field(
        default_factory=SustainedFailureThresholds
    )
    max_problem_dimensions: int = Field(default=20, ge=1, le=1_000)

    @field_validator("enabled_rules", "disabled_rules", mode="before")
    @classmethod
    def coerce_rules(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(value)
        return value

    @model_validator(mode="after")
    def validate_rule_sets(self) -> Self:
        if len(set(self.enabled_rules)) != len(self.enabled_rules):
            msg = "enabled_rules must be unique"
            raise ValueError(msg)
        if len(set(self.disabled_rules)) != len(self.disabled_rules):
            msg = "disabled_rules must be unique"
            raise ValueError(msg)
        overlap = set(self.enabled_rules).intersection(self.disabled_rules)
        if overlap:
            msg = f"rules cannot be both enabled and disabled: {sorted(r.value for r in overlap)}"
            raise ValueError(msg)
        return self

    def active_rule_ids(self) -> tuple[QualityRuleId, ...]:
        disabled = set(self.disabled_rules)
        return tuple(rule_id for rule_id in self.enabled_rules if rule_id not in disabled)

    def severity_for(self, rule_id: QualityRuleId, default: QualitySeverity) -> QualitySeverity:
        return self.severity_overrides.get(rule_id, default)

    def resolve_action(
        self,
        *,
        status: QualityStatus,
        highest_severity: QualitySeverity,
    ) -> QualityAction:
        if status is QualityStatus.PASSED:
            return QualityAction.ACCEPT
        if self.observe_only:
            return QualityAction.ACCEPT_DEGRADED
        if highest_severity is QualitySeverity.WARNING:
            return QualityAction.ACCEPT_DEGRADED
        if highest_severity is QualitySeverity.CRITICAL and self.halt_on_critical:
            return QualityAction.HALT_PIPELINE
        if highest_severity in {QualitySeverity.ERROR, QualitySeverity.CRITICAL}:
            if self.quarantine_on_error:
                return QualityAction.QUARANTINE
            if self.reject_on_error or highest_severity is QualitySeverity.CRITICAL:
                return QualityAction.REJECT
        return QualityAction.ACCEPT_DEGRADED

    def fingerprint(self) -> str:
        import hashlib

        return hashlib.sha256(canonicalize_policy(self)).hexdigest()


def default_quality_policy(
    *,
    observe_only: bool = True,
    reject_on_error: bool = False,
    halt_on_critical: bool = False,
    quarantine_on_error: bool = False,
    aggregation_window_seconds: int = 300,
    max_problem_dimensions: int = 20,
) -> QualityPolicy:
    """Version-controlled safe default policy."""

    return QualityPolicy(
        observe_only=observe_only,
        reject_on_error=reject_on_error,
        halt_on_critical=halt_on_critical,
        quarantine_on_error=quarantine_on_error,
        aggregation_window_seconds=aggregation_window_seconds,
        max_problem_dimensions=max_problem_dimensions,
        # Defaults are deliberately limited to faster market events.
        freshness_thresholds_by_event_type={
            MarketEventType.TRADE: 300,
            MarketEventType.QUOTE: 300,
            MarketEventType.BAR: 86_400,
        },
        max_ingestion_lag_by_event_type={
            MarketEventType.TRADE: 60,
            MarketEventType.QUOTE: 60,
            MarketEventType.BAR: 3_600,
        },
        max_known_to_ingested_lag_by_event_type={
            MarketEventType.TRADE: 60,
            MarketEventType.QUOTE: 60,
            MarketEventType.BAR: 3_600,
        },
    )


def canonicalize_policy(policy: QualityPolicy) -> bytes:
    payload = policy.model_dump(mode="python")
    normalized = _normalize(payload)
    return json.dumps(
        normalized,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate mapping keys."""


def _construct_mapping_unique(
    loader: yaml.SafeLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DataQualityPolicyParseError(detail="duplicate key in YAML mapping")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_unique,
)


def load_quality_policy_file(
    path_text: str,
    *,
    max_file_size_bytes: int,
) -> QualityPolicy:
    path = _resolve_policy_path(path_text)
    size = path.stat().st_size
    if size > max_file_size_bytes:
        raise DataQualityPolicyFileTooLargeError(detail="policy file exceeds max size")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataQualityPolicyParseError(detail="policy file is not valid UTF-8") from exc
    source_format: Literal["json", "yaml"] = "json" if path.suffix.lower() == ".json" else "yaml"
    data = _parse_policy_text(text, source_format=source_format)
    try:
        return QualityPolicy.model_validate(data)
    except ValueError as exc:
        raise DataQualityPolicyParseError(detail="policy schema invalid") from exc


def _resolve_policy_path(path_text: str) -> Path:
    if "://" in path_text:
        raise DataQualityPolicyPathError(detail="remote policy paths are not supported")
    path = Path(path_text).expanduser()
    if not path.exists():
        raise DataQualityPolicyNotFoundError(detail="policy file not found")
    if path.is_symlink():
        raise DataQualityPolicySymlinkRejectedError(detail="policy symlink rejected")
    if not path.is_file():
        raise DataQualityPolicyPathError(detail="policy path must be a file")
    suffix = path.suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise DataQualityPolicyPathError(detail="policy extension is not allowed")
    resolved = path.resolve()
    parent = path.parent.resolve()
    try:
        resolved.relative_to(parent)
    except ValueError as exc:
        raise DataQualityPolicyPathError(detail="policy path escapes parent directory") from exc
    return resolved


def _parse_policy_text(text: str, *, source_format: Literal["json", "yaml"]) -> dict[str, Any]:
    if source_format == "json":
        return _parse_json(text)
    return _parse_yaml(text)


def _parse_json(text: str) -> dict[str, Any]:
    def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        mapping: dict[str, Any] = {}
        for key, value in pairs:
            if key in mapping:
                raise DataQualityPolicyParseError(detail="duplicate key in JSON object")
            mapping[key] = value
        return mapping

    decoder = json.JSONDecoder(object_pairs_hook=_pairs_hook, parse_constant=_reject_constant)
    try:
        stripped = text.lstrip()
        data, index = decoder.raw_decode(stripped)
    except DataQualityPolicyParseError:
        raise
    except json.JSONDecodeError as exc:
        raise DataQualityPolicyParseError(detail="JSON parse failed") from exc
    if stripped[index:].strip():
        raise DataQualityPolicyParseError(detail="JSON trailing garbage")
    if not isinstance(data, dict):
        raise DataQualityPolicyParseError(detail="policy root must be an object")
    return data


def _parse_yaml(text: str) -> dict[str, Any]:
    loader = _UniqueKeySafeLoader(text)
    try:
        data = loader.get_single_data()
    except DataQualityPolicyParseError:
        raise
    except ConstructorError as exc:
        raise DataQualityPolicyParseError(detail="YAML parse failed") from exc
    except yaml.YAMLError as exc:
        raise DataQualityPolicyParseError(detail="YAML parse failed") from exc
    if not isinstance(data, dict):
        raise DataQualityPolicyParseError(detail="policy root must be a mapping")
    return data


def _reject_constant(value: str) -> float:
    raise DataQualityPolicyParseError(detail=f"unsupported JSON constant {value!r}")


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(_normalize_key(k)): _normalize(v) for k, v in sorted(value.items(), key=str)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (QualityRuleId, QualitySeverity, QualityStatus, QualityAction)):
        return value.value
    if isinstance(value, MarketEventType):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return value


def _normalize_key(value: Any) -> str:
    if isinstance(value, (QualityRuleId, MarketEventType)):
        return value.value
    return str(value)
