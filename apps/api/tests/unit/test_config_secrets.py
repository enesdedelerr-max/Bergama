"""Unit tests for AppSettings + SecretSettings loading policy."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.core.config import AppSettings, clear_settings_cache
from app.core.environment import AppEnvironment
from app.core.logging import is_sensitive_key, redact_mapping
from app.core.secrets import SecretSettings
from pydantic import ValidationError
from tests.conftest import (
    VALID_PROD_APP_SECRET,
    VALID_PROD_JWT_SECRET,
    make_production_secrets,
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in list(os.environ):
        if key.startswith("BERGAMA_"):
            monkeypatch.delenv(key, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_nested_env_variable_loading(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "production")
    monkeypatch.setenv("BERGAMA_DEBUG", "false")
    monkeypatch.setenv("BERGAMA_LOG_LEVEL", "INFO")
    monkeypatch.setenv("BERGAMA_SECRETS__APP_SECRET_KEY", VALID_PROD_APP_SECRET)
    monkeypatch.setenv(
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY",
        VALID_PROD_JWT_SECRET,
    )
    settings = AppSettings()
    assert settings.secrets.app_secret_key is not None
    assert settings.secrets.app_secret_key.get_secret_value() == VALID_PROD_APP_SECRET
    assert settings.secrets.bootstrap_jwt_signing_key is not None
    assert settings.secrets.bootstrap_jwt_signing_key.get_secret_value() == VALID_PROD_JWT_SECRET


def test_missing_required_production_secret_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError) as exc_info:
        AppSettings(environment=AppEnvironment.PRODUCTION, debug=False)
    err = str(exc_info.value)
    assert "required" in err.lower()
    assert VALID_PROD_APP_SECRET not in err


def test_placeholder_production_secret_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError) as exc_info:
        AppSettings(
            environment=AppEnvironment.STAGING,
            debug=False,
            secrets=SecretSettings(
                app_secret_key="password",
                bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET,
            ),
        )
    assert "placeholder" in str(exc_info.value).lower()
    assert "password" not in str(exc_info.value).split("placeholder")[0]


def test_weak_length_production_secret_fails(clean_env: None) -> None:
    with pytest.raises(ValidationError) as exc_info:
        AppSettings(
            environment=AppEnvironment.PRODUCTION,
            debug=False,
            secrets=SecretSettings(
                app_secret_key="short-but-not-placeholder",
                bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET,
            ),
        )
    assert "at least" in str(exc_info.value).lower()
    assert "short-but-not-placeholder" not in str(exc_info.value)


def test_valid_production_secret_passes(clean_env: None) -> None:
    settings = AppSettings(
        environment=AppEnvironment.PRODUCTION,
        debug=False,
        secrets=make_production_secrets(),
    )
    assert settings.secrets.app_secret_key is not None


def test_safe_summary_excludes_raw_secrets(clean_env: None) -> None:
    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        debug=False,
        secrets=make_production_secrets(),
    )
    summary = settings.safe_summary()
    blob = str(summary)
    assert VALID_PROD_APP_SECRET not in blob
    assert VALID_PROD_JWT_SECRET not in blob
    assert summary["secrets"]["app_secret_key_configured"] is True


def test_local_secrets_file_loads_when_present(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    secrets_file = tmp_path / ".secrets.env"
    secrets_file.write_text(
        "\n".join(
            [
                f"BERGAMA_SECRETS__APP_SECRET_KEY={VALID_PROD_APP_SECRET}",
                f"BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY={VALID_PROD_JWT_SECRET}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "local")
    monkeypatch.chdir(tmp_path)
    settings = AppSettings()
    assert settings.secrets.app_secret_key is not None
    assert settings.secrets.app_secret_key.get_secret_value() == VALID_PROD_APP_SECRET


def test_env_overrides_local_secrets_file(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    secrets_file = tmp_path / ".secrets.env"
    secrets_file.write_text(
        "\n".join(
            [
                "BERGAMA_SECRETS__APP_SECRET_KEY=file-only-app-secret-key-value-0001",
                "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY=file-only-jwt-signing-key-value-0001",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "local")
    monkeypatch.setenv("BERGAMA_SECRETS__APP_SECRET_KEY", VALID_PROD_APP_SECRET)
    monkeypatch.setenv(
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY",
        VALID_PROD_JWT_SECRET,
    )
    monkeypatch.chdir(tmp_path)
    settings = AppSettings()
    assert settings.secrets.app_secret_key is not None
    assert settings.secrets.app_secret_key.get_secret_value() == VALID_PROD_APP_SECRET


def test_test_profile_ignores_developer_secrets_file(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    secrets_file = tmp_path / ".secrets.env"
    secrets_file.write_text(
        f"BERGAMA_SECRETS__APP_SECRET_KEY={VALID_PROD_APP_SECRET}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.chdir(tmp_path)
    settings = AppSettings()
    assert settings.secrets.app_secret_key is None


@pytest.mark.parametrize("profile", ["staging", "production"])
def test_production_like_ignores_secrets_file(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    profile: str,
) -> None:
    secrets_file = tmp_path / ".secrets.env"
    secrets_file.write_text(
        "\n".join(
            [
                f"BERGAMA_SECRETS__APP_SECRET_KEY={VALID_PROD_APP_SECRET}",
                f"BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY={VALID_PROD_JWT_SECRET}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", profile)
    monkeypatch.setenv("BERGAMA_DEBUG", "false")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValidationError):
        AppSettings()


def test_logging_redaction_handles_secret_field_names() -> None:
    assert is_sensitive_key("app_secret_key")
    assert is_sensitive_key("bootstrap_jwt_signing_key")
    assert is_sensitive_key("signing_key")
    assert not is_sensitive_key("app_secret_key_configured")
    redacted = redact_mapping(
        {
            "app_secret_key": VALID_PROD_APP_SECRET,
            "bootstrap_jwt_signing_key": VALID_PROD_JWT_SECRET,
            "app_secret_key_configured": True,
        }
    )
    assert redacted["app_secret_key"] == "[REDACTED]"
    assert redacted["bootstrap_jwt_signing_key"] == "[REDACTED]"
    assert redacted["app_secret_key_configured"] is True
