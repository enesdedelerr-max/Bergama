"""Strict strategy configuration and deterministic fingerprinting."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.strategy.keys import strategy_sha256

_SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "apikey", "authorization")


class StrategyConfig(BaseModel):
    """Base strategy configuration. Subclasses add typed parameters only."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    config_version: str = Field(default="1.0.0", min_length=1, max_length=32)
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

    def fingerprint(self) -> str:
        return strategy_config_fingerprint(self)


def strategy_config_fingerprint(config: StrategyConfig | BaseModel | dict[str, Any]) -> str:
    """Return stable SHA-256 over typed, secret-free strategy config."""
    payload = config.model_dump(mode="python") if isinstance(config, BaseModel) else dict(config)
    _reject_sensitive_keys(payload)
    return strategy_sha256(payload)


def _reject_sensitive_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _SENSITIVE_TOKENS):
                msg = f"forbidden strategy config key {key!r}"
                raise ValueError(msg)
            _reject_sensitive_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_sensitive_keys(item)
