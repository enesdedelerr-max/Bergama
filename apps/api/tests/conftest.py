"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from app.core.config import AppSettings, clear_settings_cache
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.factory import create_app
from httpx import ASGITransport, AsyncClient

# Deterministic test-only material (>= 32 chars, not placeholder equality).
VALID_PROD_APP_SECRET = "prod-valid-app-secret-key-value-0001"
VALID_PROD_JWT_SECRET = "prod-valid-jwt-signing-key-value-0001"


def make_production_secrets() -> SecretSettings:
    """Return valid production-like secrets for tests only."""
    return SecretSettings(
        app_secret_key=VALID_PROD_APP_SECRET,
        bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET,
    )


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Isolate settings cache across tests."""
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        app_name="bergama-api-test",
        app_version="0.2.0",
        environment=AppEnvironment.TEST,
        debug=False,
        docs_enabled=True,
        openapi_enabled=True,
        log_level="WARNING",
        api_prefix="/api/v1",
        service_name="bergama-api-test",
        instance_id="test-1",
    )


@pytest.fixture
async def client(settings: AppSettings) -> AsyncIterator[AsyncClient]:
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
