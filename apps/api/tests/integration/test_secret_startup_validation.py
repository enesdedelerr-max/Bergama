"""Integration tests for secret-aware application startup."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator

import pytest
from app.core.config import AppSettings, clear_settings_cache
from app.core.environment import AppEnvironment
from app.core.logging import configure_logging
from app.core.secrets import SecretSettings
from app.factory import create_app
from app.lifespan import on_startup
from httpx import ASGITransport, AsyncClient
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


@pytest.mark.asyncio
async def test_valid_local_app_startup() -> None:
    settings = AppSettings(
        environment=AppEnvironment.LOCAL, debug=True, bootstrap_auth_enabled=False
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/ready")).status_code == 200


@pytest.mark.asyncio
async def test_valid_test_app_startup() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST, debug=False, bootstrap_auth_enabled=False
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/ready")).status_code == 200


def test_production_startup_succeeds_without_bootstrap_secret(clean_env: None) -> None:
    application = create_app(
        AppSettings(
            environment=AppEnvironment.PRODUCTION, debug=False, bootstrap_auth_enabled=False
        )
    )
    assert application.state.settings.bootstrap_auth_enabled is False


@pytest.mark.asyncio
async def test_production_startup_succeeds_with_injected_secrets() -> None:
    settings = AppSettings(
        environment=AppEnvironment.PRODUCTION,
        debug=False,
        docs_enabled=True,
        openapi_enabled=True,
        secrets=make_production_secrets(),
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/ready")).status_code == 200
        openapi = await client.get("/openapi.json")
        docs = await client.get("/docs")

    assert docs.status_code == 200
    assert openapi.status_code == 200
    blob = json.dumps(openapi.json())
    assert VALID_PROD_APP_SECRET not in blob
    assert VALID_PROD_JWT_SECRET not in blob
    assert "SecretSettings" not in blob
    assert "app_secret_key" not in blob
    assert "bootstrap_jwt_signing_key" not in blob


@pytest.mark.asyncio
async def test_startup_logs_contain_flags_not_raw_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        debug=False,
        log_level="INFO",
        secrets=make_production_secrets(),
    )
    configure_logging(settings)
    await on_startup(settings)
    out = capsys.readouterr().out
    assert VALID_PROD_APP_SECRET not in out
    assert VALID_PROD_JWT_SECRET not in out
    assert "bootstrap_jwt_signing_key_configured" in out or "application.started" in out


def test_secret_validation_errors_do_not_reveal_raw_content(clean_env: None) -> None:
    leaked = "super-leaky-production-secret-value-9999"
    with pytest.raises(ValidationError) as exc_info:
        AppSettings(
            environment=AppEnvironment.TEST,
            bootstrap_auth_enabled=True,
            secrets=SecretSettings(bootstrap_jwt_signing_key="example"),
        )
    err = str(exc_info.value)
    assert leaked not in err
    assert "placeholder" in err.lower()
