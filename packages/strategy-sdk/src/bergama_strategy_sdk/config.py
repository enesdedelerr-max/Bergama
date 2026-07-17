"""Immutable strategy configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bergama_strategy_sdk.fingerprints import configuration_fingerprint

_SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "apikey", "authorization")


class StrategyConfig(BaseModel):
    """Base strategy configuration with deterministic fingerprint."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    config_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def validate_safe_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 16:
            msg = "safe_metadata may contain at most 16 entries"
            raise ValueError(msg)
        cleaned: dict[str, str] = {}
        for key, raw in value.items():
            k = str(key).strip()
            v = str(raw).strip()
            lowered = k.lower()
            if not k or len(k) > 64 or len(v) > 256:
                msg = "safe_metadata keys/values exceed allowed bounds"
                raise ValueError(msg)
            if any(token in lowered for token in _SENSITIVE_TOKENS):
                msg = f"forbidden safe_metadata key {k!r}"
                raise ValueError(msg)
            cleaned[k] = v
        return cleaned

    def fingerprint_payload(self) -> dict[str, Any]:
        """Deterministic business config only — safe_metadata is excluded."""
        payload = self.model_dump(mode="python", exclude={"safe_metadata"})
        return {key: payload[key] for key in sorted(payload)}

    def fingerprint(self) -> str:
        return configuration_fingerprint(self.fingerprint_payload())
