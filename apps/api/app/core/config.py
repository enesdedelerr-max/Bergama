"""Typed application configuration (Pydantic Settings) — Issues #202 / #204."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.core.security import JWT_ALGORITHM_HS256, JwtAlgorithm

_ENV_PREFIX = "BERGAMA_"
_DOTENV_NAME = ".env"
_SECRETS_ENV_NAME = ".secrets.env"
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class AppSettings(BaseSettings):
    """Typed runtime configuration with a nested secret boundary."""

    model_config = SettingsConfigDict(
        env_prefix=_ENV_PREFIX,
        env_nested_delimiter="__",
        env_file=_DOTENV_NAME,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        validate_default=True,
        hide_input_in_errors=True,
    )

    app_name: str = Field(default="Bergama Trading API", min_length=1)
    app_version: str = Field(default="0.2.0", min_length=1)
    environment: AppEnvironment = Field(default=AppEnvironment.LOCAL)
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    api_prefix: str = Field(default="/api/v1")
    docs_enabled: bool = Field(default=True)
    openapi_enabled: bool = Field(default=True)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    shutdown_timeout_seconds: float = Field(default=15.0, gt=0)
    host: str = Field(default="0.0.0.0", min_length=1)
    port: int = Field(default=8000, ge=1, le=65535)

    service_name: str = Field(default="bergama-api", min_length=1)
    instance_id: str = Field(default="local-1", min_length=1)
    deployment_environment: AppEnvironment | None = Field(
        default=None,
        description="Optional override; defaults to `environment` when unset.",
    )

    secrets: SecretSettings = Field(default_factory=SecretSettings)

    # JWT bootstrap (Issue #205) — non-secret settings.
    jwt_algorithm: JwtAlgorithm = Field(default=JWT_ALGORITHM_HS256)
    jwt_issuer: str = Field(default="bergama-api", min_length=1)
    jwt_audience: str = Field(default="bergama-api", min_length=1)
    jwt_access_token_ttl_seconds: int = Field(default=900, gt=0, le=86_400)
    bootstrap_auth_enabled: bool | None = Field(
        default=None,
        description="Defaults to true for local/test and false for staging/production.",
    )

    # Health runtime (Issue #207)
    health_check_timeout_seconds: float = Field(default=2.0, gt=0)
    health_total_timeout_seconds: float = Field(default=5.0, gt=0)
    postgres_host: str | None = Field(default=None)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    redis_host: str | None = Field(default=None)
    redis_port: int = Field(default=6379, ge=1, le=65535)
    kafka_host: str | None = Field(default=None)
    kafka_port: int = Field(default=9092, ge=1, le=65535)
    postgres_required: bool | None = Field(
        default=None,
        description="Defaults to false until full DB clients are integrated.",
    )
    redis_required: bool | None = Field(
        default=None,
        description="Defaults to false until full Redis clients are integrated.",
    )
    kafka_required: bool | None = Field(
        default=None,
        description="Defaults to false until full Kafka clients are integrated.",
    )

    @field_validator("environment", "deployment_environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized not in _LOG_LEVELS:
                msg = f"unsupported log level {value!r}; expected one of {sorted(_LOG_LEVELS)}"
                raise ValueError(msg)
            return normalized
        return value

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            msg = "api_prefix must start with '/'"
            raise ValueError(msg)
        if value != "/" and value.endswith("/"):
            msg = "api_prefix must not end with '/' unless it is exactly '/'"
            raise ValueError(msg)
        return value

    @field_validator("app_name", "app_version", "service_name", "instance_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "value must be non-empty"
            raise ValueError(msg)
        return value.strip()

    @model_validator(mode="after")
    def enforce_environment_semantics(self) -> Self:
        if self.deployment_environment is None:
            object.__setattr__(self, "deployment_environment", self.environment)

        if self.environment is AppEnvironment.PRODUCTION and self.debug:
            msg = "BERGAMA_DEBUG must be false when BERGAMA_ENVIRONMENT=production"
            raise ValueError(msg)

        if self.environment is AppEnvironment.STAGING and self.debug:
            msg = "BERGAMA_DEBUG must be false when BERGAMA_ENVIRONMENT=staging"
            raise ValueError(msg)

        if self.environment is AppEnvironment.PRODUCTION and self.log_level == "DEBUG":
            msg = "BERGAMA_LOG_LEVEL=DEBUG is not allowed in production"
            raise ValueError(msg)

        enabled = self.bootstrap_auth_enabled
        if enabled is None:
            enabled = self.environment in {AppEnvironment.LOCAL, AppEnvironment.TEST}
            object.__setattr__(self, "bootstrap_auth_enabled", enabled)

        if enabled and self.environment.is_production_like:
            msg = (
                "BERGAMA_BOOTSTRAP_AUTH_ENABLED must be false when "
                "BERGAMA_ENVIRONMENT is staging or production"
            )
            raise ValueError(msg)

        if enabled:
            self.secrets.validate_bootstrap_signing_key()

        # External deps stay optional until full clients land (#208+).
        # Staging/production must set BERGAMA_*_REQUIRED explicitly to enforce.
        if self.postgres_required is None:
            object.__setattr__(self, "postgres_required", False)
        if self.redis_required is None:
            object.__setattr__(self, "redis_required", False)
        if self.kafka_required is None:
            object.__setattr__(self, "kafka_required", False)

        if self.health_total_timeout_seconds < self.health_check_timeout_seconds:
            msg = (
                "BERGAMA_HEALTH_TOTAL_TIMEOUT_SECONDS must be >= "
                "BERGAMA_HEALTH_CHECK_TIMEOUT_SECONDS"
            )
            raise ValueError(msg)

        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Priority: init > env > `.env` (local) > `.secrets.env` (local) > file secrets.

        Staging/test/production never load `.env` or `.secrets.env`.
        """
        sources: list[PydanticBaseSettingsSource] = [init_settings, env_settings]
        if _should_load_dotenv():
            sources.append(dotenv_settings)
        if _should_load_secrets_file():
            sources.append(
                DotEnvSettingsSource(
                    settings_cls,
                    env_file=_SECRETS_ENV_NAME,
                    env_file_encoding="utf-8",
                )
            )
        sources.append(file_secret_settings)
        return tuple(sources)

    def safe_summary(self) -> dict[str, Any]:
        """Operational summary with no secret material."""
        deployment = self.deployment_environment or self.environment
        summary: dict[str, Any] = {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment.value,
            "deployment_environment": deployment.value,
            "debug": self.debug,
            "log_level": self.log_level,
            "api_prefix": self.api_prefix,
            "docs_enabled": self.docs_enabled,
            "openapi_enabled": self.openapi_enabled,
            "request_timeout_seconds": self.request_timeout_seconds,
            "shutdown_timeout_seconds": self.shutdown_timeout_seconds,
            "service_name": self.service_name,
            "instance_id": self.instance_id,
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_issuer": self.jwt_issuer,
            "jwt_audience": self.jwt_audience,
            "jwt_access_token_ttl_seconds": self.jwt_access_token_ttl_seconds,
            "bootstrap_auth_enabled": self.bootstrap_auth_enabled,
            "health_check_timeout_seconds": self.health_check_timeout_seconds,
            "health_total_timeout_seconds": self.health_total_timeout_seconds,
            "postgres_required": self.postgres_required,
            "redis_required": self.redis_required,
            "kafka_required": self.kafka_required,
            "postgres_configured": bool(self.postgres_host),
            "redis_configured": bool(self.redis_host),
            "kafka_configured": bool(self.kafka_host),
            "secrets": self.secrets.safe_summary(),
        }
        return summary


def _resolved_environment_from_process() -> AppEnvironment | None:
    raw = os.environ.get(f"{_ENV_PREFIX}ENVIRONMENT")
    if raw is None:
        return None
    try:
        return AppEnvironment(raw.strip().lower())
    except ValueError:
        return None


def _should_load_dotenv() -> bool:
    """Deterministic dotenv gate using process env only (no .env peek for profile)."""
    resolved = _resolved_environment_from_process()
    if resolved is None:
        return Path(_DOTENV_NAME).is_file()
    return resolved.loads_dotenv and Path(_DOTENV_NAME).is_file()


def _should_load_secrets_file() -> bool:
    """Load `.secrets.env` only for the local profile when the file exists."""
    resolved = _resolved_environment_from_process()
    if resolved is None:
        # Unset profile behaves like local for developer ergonomics.
        return Path(_SECRETS_ENV_NAME).is_file()
    return resolved is AppEnvironment.LOCAL and Path(_SECRETS_ENV_NAME).is_file()


@lru_cache
def _cached_settings() -> AppSettings:
    return AppSettings()


def get_settings() -> AppSettings:
    """Return cached application settings."""
    return _cached_settings()


def clear_settings_cache() -> None:
    """Reset the settings cache (required for isolated tests)."""
    _cached_settings.cache_clear()


def load_settings(**overrides: Any) -> AppSettings:
    """Build settings without using the process cache (tests / explicit DI)."""
    return AppSettings(**overrides)


# Backward-compatible alias used by Issue #201 call sites during transition.
Settings = AppSettings
