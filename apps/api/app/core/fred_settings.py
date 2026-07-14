"""Nested FRED macro-data settings (Issue #304B)."""

from __future__ import annotations

from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

_DEFAULT_BASE_URL = "https://api.stlouisfed.org"


class FredSettings(BaseModel):
    """FRED REST connector configuration. Disabled by default."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    base_url: str = Field(default=_DEFAULT_BASE_URL, min_length=1)
    api_key: SecretStr | None = None
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    connect_timeout_seconds: float = Field(default=5.0, gt=0)
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_initial_delay_seconds: float = Field(default=0.25, ge=0)
    retry_max_delay_seconds: float = Field(default=8.0, ge=0)
    retry_after_max_seconds: float = Field(default=30.0, gt=0)
    max_pages: int = Field(default=20, ge=1, le=500)
    max_results_per_page: int = Field(default=1000, ge=1, le=100_000)
    user_agent: str = Field(default="bergama-api/0.2.0 (+fred)", min_length=1)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        text = value.strip().rstrip("/")
        parsed = urlparse(text)
        if parsed.scheme != "https" or not parsed.netloc:
            msg = "BERGAMA_FRED__BASE_URL must use https and include host"
            raise ValueError(msg)
        return text

    @field_validator("api_key", mode="before")
    @classmethod
    def normalize_api_key(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            raw = value.get_secret_value()
        elif isinstance(value, str):
            raw = value
        else:
            return value
        if raw == "":
            return None
        if raw != raw.strip():
            msg = "BERGAMA_FRED__API_KEY must not include leading/trailing whitespace"
            raise ValueError(msg)
        return raw

    @field_validator("user_agent")
    @classmethod
    def strip_user_agent(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "user_agent must be non-empty"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.retry_initial_delay_seconds > self.retry_max_delay_seconds:
            msg = "retry_initial_delay_seconds must be <= retry_max_delay_seconds"
            raise ValueError(msg)
        if self.connect_timeout_seconds > self.request_timeout_seconds:
            msg = "connect_timeout_seconds must be <= request_timeout_seconds"
            raise ValueError(msg)
        if self.enabled:
            if self.api_key is None:
                msg = "BERGAMA_FRED__API_KEY is required when fred is enabled"
                raise ValueError(msg)
            key = self.api_key.get_secret_value()
            if len(key) < 8:
                msg = "BERGAMA_FRED__API_KEY is too short"
                raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "api_key_configured": self.api_key is not None,
            "request_timeout_seconds": self.request_timeout_seconds,
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "max_retries": self.max_retries,
            "max_pages": self.max_pages,
            "max_results_per_page": self.max_results_per_page,
        }
