"""Application-scoped async SEC EDGAR HTTP client (Issue #304C)."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger, structured_extra
from app.core.sec_settings import SecSettings
from app.infrastructure.sec.errors import SecNotConfiguredError
from app.infrastructure.sec.rate_limit import (
    AsyncSleeper,
    MinIntervalRateLimiter,
    default_sleeper,
)
from app.infrastructure.sec.retry import SecHttpRetryPolicy, request_with_retries

logger = get_logger(__name__)


class SecHttpClient:
    """Reusable AsyncClient with SEC User-Agent and conservative rate limiting."""

    def __init__(
        self,
        settings: SecSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
        rate_limiter: MinIntervalRateLimiter | None = None,
    ) -> None:
        if not settings.enabled:
            raise SecNotConfiguredError("sec is disabled")
        self._settings = settings
        self._sleeper = sleeper
        self._user_agent = settings.resolved_user_agent()
        self._retry = SecHttpRetryPolicy(
            max_attempts=settings.max_retries,
            initial_delay_seconds=settings.retry_initial_delay_seconds,
            max_delay_seconds=settings.retry_max_delay_seconds,
            retry_after_max_seconds=settings.retry_after_max_seconds,
        )
        self._rate_limiter = rate_limiter or MinIntervalRateLimiter(
            min_interval_seconds=settings.min_request_interval_seconds,
            sleeper=sleeper,
        )
        timeout = httpx.Timeout(
            timeout=settings.request_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": self._user_agent,
            },
            transport=transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        )
        self._closed = False

    @property
    def settings(self) -> SecSettings:
        return self._settings

    @property
    def user_agent(self) -> str:
        return self._user_agent

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        await self._rate_limiter.acquire()

        async def _op() -> httpx.Response:
            return await self._client.get(path, params=params or None)

        logger.debug(
            "sec http get",
            extra=structured_extra(
                event="sec.http.get",
                source="sec_http",
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
