"""Immutable feature snapshot — sole SDK feature input."""

from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bergama_strategy_sdk.fingerprints import feature_fingerprint
from bergama_strategy_sdk.serialization import canonical_json_bytes


class FeatureValue(BaseModel):
    """One normalized deterministic feature value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_id: str = Field(min_length=1, max_length=128)
    schema_id: str = Field(min_length=1, max_length=128)
    schema_version: str = Field(min_length=1, max_length=32)
    value: Decimal
    unit: str | None = Field(default=None, max_length=32)

    @field_validator("feature_id", "schema_id")
    @classmethod
    def strip_ids(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "feature identifiers must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("value", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal:
        if isinstance(value, Decimal):
            dec = value
        elif isinstance(value, (int, str)):
            dec = Decimal(str(value))
        else:
            msg = "feature values must be Decimal-compatible"
            raise TypeError(msg)
        if dec.is_nan() or dec.is_infinite():
            msg = "NaN/Infinity feature values are not allowed"
            raise ValueError(msg)
        return dec.normalize()


class FeatureSnapshot(BaseModel):
    """Host-assembled immutable feature input for strategy evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_schema_version: str = Field(min_length=1, max_length=32)
    instrument_key: str = Field(min_length=1, max_length=128)
    features: tuple[FeatureValue, ...] = Field(min_length=1)
    snapshot_id: str = Field(min_length=1, max_length=128)

    @field_validator("instrument_key", "snapshot_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "snapshot identifiers must be non-empty"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def validate_unique_sorted_features(self) -> Self:
        seen: set[str] = set()
        for feature in self.features:
            if feature.feature_id in seen:
                msg = f"duplicate feature_id {feature.feature_id!r}"
                raise ValueError(msg)
            seen.add(feature.feature_id)
        return self

    @property
    def canonical_features(self) -> tuple[FeatureValue, ...]:
        return tuple(sorted(self.features, key=lambda item: item.feature_id))

    def fingerprint_payload(self) -> dict[str, object]:
        return {
            "feature_schema_version": self.feature_schema_version,
            "features": [
                {
                    "feature_id": feature.feature_id,
                    "schema_id": feature.schema_id,
                    "schema_version": feature.schema_version,
                    "unit": feature.unit,
                    "value": format(feature.value.normalize(), "f"),
                }
                for feature in self.canonical_features
            ],
            "instrument_key": self.instrument_key,
            "snapshot_id": self.snapshot_id,
        }

    def fingerprint(self) -> str:
        return feature_fingerprint(self.fingerprint_payload())

    def payload_byte_length(self) -> int:
        return len(canonical_json_bytes(self.fingerprint_payload()))
