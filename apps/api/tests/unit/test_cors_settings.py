"""CORS allowlist parser tests (Sprint 15 WS1 / #168)."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.cors_settings import (
    CorsSettings,
    normalize_cors_origin,
    parse_cors_allowed_origins,
)
from app.core.environment import AppEnvironment
from pydantic import ValidationError


def test_normalize_strips_trailing_slash() -> None:
    assert normalize_cors_origin("http://localhost:3000/") == "http://localhost:3000"


def test_parse_empty_and_unset_deny_all() -> None:
    assert parse_cors_allowed_origins(None) == []
    assert parse_cors_allowed_origins("") == []
    assert parse_cors_allowed_origins("   ") == []
    assert CorsSettings().normalized_origins() == []


def test_parse_comma_separated_origins() -> None:
    assert parse_cors_allowed_origins("http://localhost:3000, https://console.example.com/") == [
        "http://localhost:3000",
        "https://console.example.com",
    ]


def test_reject_wildcard() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        parse_cors_allowed_origins("*")
    with pytest.raises(ValueError, match="wildcard"):
        parse_cors_allowed_origins("https://*.example.com")


def test_reject_path_query_fragment() -> None:
    with pytest.raises(ValueError, match="path"):
        normalize_cors_origin("http://localhost:3000/app")
    with pytest.raises(ValueError, match="query or fragment"):
        normalize_cors_origin("http://localhost:3000?x=1")
    with pytest.raises(ValueError, match="query or fragment"):
        normalize_cors_origin("http://localhost:3000#x")


def test_reject_invalid_scheme_and_userinfo() -> None:
    with pytest.raises(ValueError, match="http or https"):
        normalize_cors_origin("ftp://localhost")
    with pytest.raises(ValueError, match="userinfo"):
        normalize_cors_origin("http://user:pass@localhost:3000")


def test_app_settings_rejects_invalid_cors_allowlist() -> None:
    with pytest.raises(ValidationError):
        AppSettings(
            environment=AppEnvironment.TEST,
            bootstrap_auth_enabled=False,
            cors={"allowed_origins": "*"},
        )


def test_app_settings_accepts_valid_cors_allowlist() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        cors={"allowed_origins": "http://localhost:3000"},
    )
    assert settings.cors.normalized_origins() == ["http://localhost:3000"]
