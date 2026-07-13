"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.config.settings import Settings
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_name="bergama-api-test",
        environment="paper",
        debug=True,
        log_json=False,
        log_level="WARNING",
    )


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
