"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from app.core.config import AppSettings, clear_settings_cache
from app.core.environment import AppEnvironment
from app.factory import create_app
from httpx import ASGITransport, AsyncClient


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
