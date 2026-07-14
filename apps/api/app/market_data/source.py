"""Provider / source provenance — bounded extras only."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_MAX_EXTRAS = 32
_MAX_EXTRA_KEY = 64
_MAX_EXTRA_VALUE = 512


class SourceReference(BaseModel):
    """Provider-side identity retained without becoming canonical."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1, max_length=64)
    source_symbol: str | None = Field(default=None, max_length=128)
    source_instrument_id: str | None = Field(default=None, max_length=128)
    source_event_id: str | None = Field(default=None, max_length=256)
    source_payload_ref: str | None = Field(
        default=None,
        max_length=512,
        description="Opaque reference/URI/hash to raw payload — not the payload body",
    )
    extras: dict[str, str] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def strip_provider(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "provider must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator(
        "source_symbol",
        "source_instrument_id",
        "source_event_id",
        "source_payload_ref",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        return text

    @model_validator(mode="after")
    def validate_extras(self) -> Self:
        if len(self.extras) > _MAX_EXTRAS:
            msg = f"source.extras may contain at most {_MAX_EXTRAS} entries"
            raise ValueError(msg)
        cleaned: dict[str, str] = {}
        for key, value in self.extras.items():
            k = str(key).strip()
            v = str(value).strip()
            if not k or len(k) > _MAX_EXTRA_KEY or len(v) > _MAX_EXTRA_VALUE:
                msg = "source.extras keys/values exceed allowed bounds"
                raise ValueError(msg)
            # Reject provider secrets or large blobs disguised as extras.
            lowered = k.lower()
            if any(token in lowered for token in ("password", "secret", "token", "api_key")):
                msg = f"forbidden source.extras key {k!r}"
                raise ValueError(msg)
            cleaned[k] = v
        object.__setattr__(self, "extras", cleaned)
        return self
