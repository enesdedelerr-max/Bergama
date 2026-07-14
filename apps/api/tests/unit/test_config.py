"""Unit tests for AppSettings configuration layer."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pytest
from app.core.config import (
    AppSettings,
    clear_settings_cache,
    get_settings,
    load_settings,
)
from app.core.environment import AppEnvironment
from pydantic import ValidationError


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in list(os.environ):
        if key.startswith("BERGAMA_"):
            monkeypatch.delenv(key, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_default_local_settings_load(clean_env: None) -> None:
    settings = AppSettings(bootstrap_auth_enabled=False)
    assert settings.environment is AppEnvironment.LOCAL
    assert settings.app_name
    assert settings.app_version
    assert settings.api_prefix == "/api/v1"
    assert settings.docs_enabled is True
    assert settings.openapi_enabled is True


def test_env_vars_override_defaults(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "staging")
    monkeypatch.setenv("BERGAMA_APP_NAME", "Override API")
    monkeypatch.setenv("BERGAMA_DEBUG", "false")
    monkeypatch.setenv("BERGAMA_API_PREFIX", "/api/v2")
    monkeypatch.setenv(
        "BERGAMA_SECRETS__APP_SECRET_KEY",
        "prod-valid-app-secret-key-value-0001",
    )
    monkeypatch.setenv(
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY",
        "prod-valid-jwt-signing-key-value-0001",
    )
    settings = AppSettings()
    assert settings.environment is AppEnvironment.STAGING
    assert settings.app_name == "Override API"
    assert settings.api_prefix == "/api/v2"


def test_unknown_environment_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment="qa")


def test_production_with_debug_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment=AppEnvironment.PRODUCTION, debug=True)


def test_staging_with_debug_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment=AppEnvironment.STAGING, debug=True)


def test_production_debug_log_level_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment=AppEnvironment.PRODUCTION, debug=False, log_level="DEBUG")


def test_invalid_api_prefix_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(api_prefix="api/v1")
    with pytest.raises(ValidationError):
        AppSettings(api_prefix="/api/v1/")


def test_zero_or_negative_timeout_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(request_timeout_seconds=0)
    with pytest.raises(ValidationError):
        AppSettings(shutdown_timeout_seconds=-1)


def test_unsupported_log_level_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(log_level="VERBOSE")  # type: ignore[arg-type]


def test_dotenv_gate_skips_for_test_profile(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    from app.core import config as config_module

    assert config_module._should_load_dotenv() is False


def test_provider_caching(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BERGAMA_BOOTSTRAP_AUTH_ENABLED", "false")
    clear_settings_cache()
    assert get_settings() is get_settings()


def test_cache_reset_isolates_tests(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BERGAMA_BOOTSTRAP_AUTH_ENABLED", "false")
    clear_settings_cache()
    first = get_settings()
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "staging")
    monkeypatch.setenv("BERGAMA_DEBUG", "false")
    monkeypatch.setenv(
        "BERGAMA_SECRETS__APP_SECRET_KEY",
        "prod-valid-app-secret-key-value-0001",
    )
    monkeypatch.setenv(
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY",
        "prod-valid-jwt-signing-key-value-0001",
    )
    clear_settings_cache()
    second = get_settings()
    assert first is not second
    assert second.environment is AppEnvironment.STAGING


def test_load_settings_bypasses_cache(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.conftest import make_production_secrets

    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BERGAMA_BOOTSTRAP_AUTH_ENABLED", "false")
    clear_settings_cache()
    cached = get_settings()
    isolated = load_settings(
        environment=AppEnvironment.STAGING,
        debug=False,
        secrets=make_production_secrets(),
    )
    assert isolated.environment is AppEnvironment.STAGING
    assert cached.environment is AppEnvironment.TEST


def test_safe_summary_has_no_secret_values(clean_env: None) -> None:
    from tests.conftest import VALID_PROD_APP_SECRET, make_production_secrets

    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        debug=False,
        secrets=make_production_secrets(),
    )
    summary: dict[str, Any] = settings.safe_summary()
    blob = str(summary)
    assert VALID_PROD_APP_SECRET not in blob
    assert "get_secret_value" not in blob
    assert summary["secrets"]["app_secret_key_configured"] is True
    assert summary["secrets"]["bootstrap_jwt_signing_key_configured"] is True
    assert summary["environment"] == "staging"


def test_empty_app_version_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(app_version="   ")


def test_extra_fields_forbidden(clean_env: None) -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment=AppEnvironment.TEST, unknown_field="x")  # type: ignore[call-arg]
