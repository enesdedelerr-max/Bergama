"""Application-scoped async Benzinga HTTP client (Issue #304D)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.benzinga_settings import BenzingaSettings
from app.core.logging import get_logger, structured_extra
from app.infrastructure.benzinga.errors import BenzingaNotConfiguredError
from app.infrastructure.benzinga.pagination import sanitize_url
from app.infrastructure.benzinga.retry import (
    AsyncSleeper,
    BenzingaHttpRetryPolicy,
    default_sleeper,
    request_with_retries,
)

logger = get_logger(__name__)

_AUTH_HEADER = "Authorization"


class BenzingaHttpClient:
    """Reusable AsyncClient authenticated via Authorization token header only."""

    def __init__(
        self,
        settings: BenzingaSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
    ) -> None:
        if not settings.enabled:
            raise BenzingaNotConfiguredError("benzinga is disabled")
        if settings.api_key is None:
            raise BenzingaNotConfiguredError("benzinga api key is not configured")
        self._settings = settings
        self._sleeper = sleeper
        self._retry = BenzingaHttpRetryPolicy(
            max_attempts=settings.max_retries,
            initial_delay_seconds=settings.retry_initial_delay_seconds,
            max_delay_seconds=settings.retry_max_delay_seconds,
            max_retry_after_seconds=settings.max_retry_after_seconds,
        )
        timeout = httpx.Timeout(
            timeout=settings.request_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        token = settings.api_key.get_secret_value()
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": settings.user_agent,
                _AUTH_HEADER: f"token {token}",
            },
            transport=transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._closed = False

    @property
    def settings(self) -> BenzingaSettings:
        return self._settings

    def build_params(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build query params without ever attaching credentials."""
        merged: dict[str, Any] = {}
        if params:
            for key, value in params.items():
                if key.lower() in {"token", "api_key", "apikey", "access_token"}:
                    continue
                if value is not None:
                    merged[key] = value
        return merged

    def sanitized_request_url(self, path: str, params: dict[str, Any]) -> str:
        """Absolute URL with credentials stripped (for logs / source refs)."""
        query = urlencode([(k, v) for k, v in params.items()])
        base = self._settings.base_url.rstrip("/")
        raw = f"{base}{path}?{query}" if query else f"{base}{path}"
        return sanitize_url(raw)

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        safe_params = self.build_params(params)
        sanitized = self.sanitized_request_url(path, safe_params)

        async def _op() -> httpx.Response:
            return await self._client.get(path, params=safe_params or None)

        logger.debug(
            "benzinga http get",
            extra=structured_extra(
                event="benzinga.http.get",
                source="benzinga_http",
                path=path,
                url=sanitized,
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
