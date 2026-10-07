"""Unit tests for Intelligence Run database settings (WS1)."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings, load_settings
from app.core.database_settings import DatabaseSettings
from app.core.environment import AppEnvironment
from pydantic import ValidationError


def test_database_settings_default_unconfigured() -> None:
    settings = DatabaseSettings()
    assert settings.url is None
    assert settings.safe_summary() == {"configured": False, "driver": None}


def test_database_settings_accepts_psycopg_dsn() -> None:
    url = "postgresql+psycopg://bergama:bergama@localhost:5432/bergama_test"
    settings = DatabaseSettings(url=url)
    assert settings.url == url
    assert settings.safe_summary() == {
        "configured": True,
        "driver": "postgresql+psycopg",
    }


def test_database_settings_rejects_non_psycopg_dsn() -> None:
    with pytest.raises(ValidationError):
        DatabaseSettings(url="postgresql://bergama:bergama@localhost:5432/bergama_test")
    with pytest.raises(ValidationError):
        DatabaseSettings(url="postgresql+asyncpg://bergama:bergama@localhost:5432/bergama_test")


def test_app_settings_nested_database_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = "postgresql+psycopg://bergama:bergama@localhost:5432/bergama_test"
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BERGAMA_DATABASE__URL", url)
    monkeypatch.setenv("BERGAMA_BOOTSTRAP_AUTH_ENABLED", "false")
    settings = load_settings()
    assert settings.database.url == url
    assert settings.safe_summary()["database"]["configured"] is True


def test_app_settings_database_override() -> None:
    url = "postgresql+psycopg://bergama:bergama@localhost:5432/bergama_test"
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        database=DatabaseSettings(url=url),
    )
    assert settings.database.url == url
