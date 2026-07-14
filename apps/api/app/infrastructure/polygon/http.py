"""Application-scoped async Polygon HTTP client."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger, structured_extra
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.polygon.errors import PolygonNotConfiguredError
from app.infrastructure.polygon.retry import (
    AsyncSleeper,
    PolygonHttpRetryPolicy,
    default_sleeper,
    request_with_retries,
)

logger = get_logger(__name__)


class PolygonHttpClient:
    """Reusable AsyncClient with Authorization Bearer auth."""

    def __init__(
        self,
        settings: PolygonSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
    ) -> None:
        if not settings.enabled:
            raise PolygonNotConfiguredError("polygon is disabled")
        if settings.api_key is None:
            raise PolygonNotConfiguredError("polygon api key is not configured")
        self._settings = settings
        self._sleeper = sleeper
        self._retry = PolygonHttpRetryPolicy(
            max_attempts=settings.max_retries,
            initial_delay_seconds=settings.retry_initial_delay_seconds,
            max_delay_seconds=settings.retry_max_delay_seconds,
            retry_after_max_seconds=settings.retry_after_max_seconds,
        )
        timeout = httpx.Timeout(
            timeout=settings.request_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        headers = {
            "Accept": "application/json",
            "User-Agent": settings.user_agent,
            "Authorization": f"Bearer {settings.api_key.get_secret_value()}",
        }
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        self._closed = False

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    @property
    def settings(self) -> PolygonSettings:
        return self._settings

    async def get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        async def _op() -> httpx.Response:
            return await self._client.get(url, params=params)

        logger.debug(
            "polygon http get",
            extra=structured_extra(
                event="polygon.http.get",
                source="polygon_http",
                path=url.split("?", 1)[0],
            ),
        )
        return await request_with_retries(
            operation=_op,
            policy=self._retry,
            sleeper=self._sleeper,
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._client.aclose()
