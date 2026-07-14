"""Nested SEC EDGAR filings settings (Issue #304C)."""

from __future__ import annotations

import re
from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_DEFAULT_DATA_BASE_URL = "https://data.sec.gov"
_DEFAULT_ARCHIVES_BASE_URL = "https://www.sec.gov"
_PLACEHOLDER_EMAILS = frozenset(
    {
        "admin@example.com",
        "contact@example.com",
        "user@example.com",
        "noreply@example.com",
        "test@example.com",
    }
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_GENERIC_UA_MARKERS = frozenset(
    {
        "mozilla/",
        "chrome/",
        "safari/",
        "curl/",
        "python-requests",
        "httpx/",
        "wget/",
    }
)


class SecSettings(BaseModel):
    """SEC EDGAR submissions connector configuration. Disabled by default."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    base_url: str = Field(default=_DEFAULT_DATA_BASE_URL, min_length=1)
    archives_base_url: str = Field(default=_DEFAULT_ARCHIVES_BASE_URL, min_length=1)
    application_name: str = Field(default="BergamaTrading", min_length=1, max_length=128)
    contact_email: str | None = None
    user_agent: str | None = None
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    connect_timeout_seconds: float = Field(default=5.0, gt=0)
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_initial_delay_seconds: float = Field(default=0.25, ge=0)
    retry_max_delay_seconds: float = Field(default=8.0, ge=0)
    retry_after_max_seconds: float = Field(default=30.0, gt=0)
    # Conservative vs SEC fair-access ceiling of 10 req/s.
    min_request_interval_seconds: float = Field(default=0.2, ge=0.1, le=10.0)
    max_filings_per_request: int = Field(default=100, ge=1, le=1000)

    @field_validator("base_url", "archives_base_url")
    @classmethod
    def validate_https_url(cls, value: str) -> str:
        text = value.strip().rstrip("/")
        parsed = urlparse(text)
        if parsed.scheme != "https" or not parsed.netloc:
            msg = "SEC URLs must use https and include host"
            raise ValueError(msg)
        host = parsed.netloc.lower()
        if host not in {"data.sec.gov", "www.sec.gov"} and not host.endswith(".sec.gov"):
            msg = "SEC URLs must use an official sec.gov host"
            raise ValueError(msg)
        return text

    @field_validator("application_name")
    @classmethod
    def strip_application_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "application_name must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("contact_email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text == "":
            return None
        return text

    @field_validator("user_agent", mode="before")
    @classmethod
    def normalize_user_agent(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text == "":
            return None
        return text

    def resolved_user_agent(self) -> str:
        if self.user_agent:
            return self.user_agent
        if self.contact_email:
            return f"{self.application_name} {self.contact_email}"
        msg = "SEC User-Agent requires user_agent or contact_email"
        raise ValueError(msg)

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.retry_initial_delay_seconds > self.retry_max_delay_seconds:
            msg = "retry_initial_delay_seconds must be <= retry_max_delay_seconds"
            raise ValueError(msg)
        if self.connect_timeout_seconds > self.request_timeout_seconds:
            msg = "connect_timeout_seconds must be <= request_timeout_seconds"
            raise ValueError(msg)
        if self.enabled:
            if self.contact_email is None and self.user_agent is None:
                msg = (
                    "BERGAMA_SEC__CONTACT_EMAIL or BERGAMA_SEC__USER_AGENT is required "
                    "when sec is enabled"
                )
                raise ValueError(msg)
            if self.contact_email is not None:
                if not _EMAIL_RE.match(self.contact_email):
                    msg = "BERGAMA_SEC__CONTACT_EMAIL must be a valid email"
                    raise ValueError(msg)
                if self.contact_email.lower() in _PLACEHOLDER_EMAILS:
                    msg = "BERGAMA_SEC__CONTACT_EMAIL must not be a placeholder example.com address"
                    raise ValueError(msg)
            try:
                ua = self.resolved_user_agent()
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            lowered = ua.lower()
            if len(ua) < 8:
                msg = "SEC User-Agent is too short"
                raise ValueError(msg)
            if any(marker in lowered for marker in _GENERIC_UA_MARKERS):
                msg = "SEC User-Agent must not be a generic browser/HTTP client identity"
                raise ValueError(msg)
            if "@" not in ua:
                msg = "SEC User-Agent must include a contact email"
                raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "archives_base_url": self.archives_base_url,
            "application_name": self.application_name,
            "contact_email_configured": self.contact_email is not None,
            "user_agent_configured": self.user_agent is not None or self.contact_email is not None,
            "request_timeout_seconds": self.request_timeout_seconds,
            "min_request_interval_seconds": self.min_request_interval_seconds,
            "max_retries": self.max_retries,
            "max_filings_per_request": self.max_filings_per_request,
        }
