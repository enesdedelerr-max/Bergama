"""Application-scoped async Finnhub HTTP client (Issue #304A)."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.finnhub_settings import FinnhubSettings
from app.core.logging import get_logger, structured_extra
from app.infrastructure.finnhub.errors import FinnhubNotConfiguredError
from app.infrastructure.finnhub.retry import (
    AsyncSleeper,
    FinnhubHttpRetryPolicy,
    default_sleeper,
    request_with_retries,
)

logger = get_logger(__name__)

_TOKEN_HEADER = "X-Finnhub-Token"


class FinnhubHttpClient:
    """Reusable AsyncClient authenticated via X-Finnhub-Token (never query token)."""

    def __init__(
        self,
        settings: FinnhubSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
    ) -> None:
        if not settings.enabled:
            raise FinnhubNotConfiguredError("finnhub is disabled")
        if settings.api_key is None:
            raise FinnhubNotConfiguredError("finnhub api key is not configured")
        self._settings = settings
        self._sleeper = sleeper
        self._retry = FinnhubHttpRetryPolicy(
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
            _TOKEN_HEADER: settings.api_key.get_secret_value(),
        }
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._closed = False

    @property
    def settings(self) -> FinnhubSettings:
        return self._settings

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        safe_params = dict(params or {})
        # Never allow token in query params.
        for forbidden in ("token", "api_key", "apikey"):
            safe_params.pop(forbidden, None)

        async def _op() -> httpx.Response:
            return await self._client.get(path, params=safe_params or None)

        logger.debug(
            "finnhub http get",
            extra=structured_extra(
                event="finnhub.http.get",
                source="finnhub_http",
                path=path.split("?", 1)[0],
            ),
        )
        return await request_with_retries(
            operation=_op,
            policy=self._retry,
            max_attempts=self._settings.max_retries,
            sleeper=self._sleeper,
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._client.aclose()
