"""Integration tests: AppSettings with the FastAPI app factory."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings, clear_settings_cache, get_settings
from app.core.environment import AppEnvironment
from app.factory import create_app
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError


async def test_app_starts_with_explicit_settings() -> None:
    from tests.conftest import make_production_secrets

    settings = AppSettings(
        app_name="Configured API",
        app_version="9.9.9",
        environment=AppEnvironment.STAGING,
        debug=False,
        docs_enabled=True,
        openapi_enabled=True,
        log_level="ERROR",
        api_prefix="/api/v1",
        service_name="configured",
        instance_id="i-1",
        secrets=make_production_secrets(),
    )
    application = create_app(settings)
    assert application.title == "Configured API"
    assert application.version == "9.9.9"

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        ready = await client.get("/ready")
        docs = await client.get("/docs")
        openapi = await client.get("/openapi.json")

    assert health.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["environment"] == "staging"
    assert docs.status_code == 200
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "Configured API"
    assert openapi.json()["info"]["version"] == "9.9.9"


async def test_docs_and_openapi_follow_settings_disabled() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        docs_enabled=False,
        openapi_enabled=False,
        debug=False,
        bootstrap_auth_enabled=False,
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        docs = await client.get("/docs")
        openapi = await client.get("/openapi.json")
        health = await client.get("/health")

    assert docs.status_code == 404
    assert openapi.status_code == 404
    assert health.status_code == 200


async def test_invalid_production_configuration_prevents_app_creation() -> None:
    with pytest.raises(ValidationError):
        create_app(AppSettings(environment=AppEnvironment.PRODUCTION, debug=True))


async def test_app_factory_uses_cached_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BERGAMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BERGAMA_APP_NAME", "from-env-api")
    monkeypatch.setenv("BERGAMA_DEBUG", "false")
    monkeypatch.setenv("BERGAMA_BOOTSTRAP_AUTH_ENABLED", "false")
    clear_settings_cache()
    settings = get_settings()
    application = create_app()
    assert application.state.container.settings is settings
    assert application.title == "from-env-api"
