"""Application-scoped async FRED HTTP client (Issue #304B)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.fred_settings import FredSettings
from app.core.logging import get_logger, structured_extra
from app.infrastructure.fred.errors import FredNotConfiguredError
from app.infrastructure.fred.pagination import sanitize_url
from app.infrastructure.fred.retry import (
    AsyncSleeper,
    FredHttpRetryPolicy,
    default_sleeper,
    request_with_retries,
)

logger = get_logger(__name__)


class FredHttpClient:
    """Reusable AsyncClient. Auth uses documented query api_key (never logged)."""

    def __init__(
        self,
        settings: FredSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
    ) -> None:
        if not settings.enabled:
            raise FredNotConfiguredError("fred is disabled")
        if settings.api_key is None:
            raise FredNotConfiguredError("fred api key is not configured")
        self._settings = settings
        self._sleeper = sleeper
        self._api_key = settings.api_key.get_secret_value()
        self._retry = FredHttpRetryPolicy(
            max_attempts=settings.max_retries,
            initial_delay_seconds=settings.retry_initial_delay_seconds,
            max_delay_seconds=settings.retry_max_delay_seconds,
            retry_after_max_seconds=settings.retry_after_max_seconds,
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
                "User-Agent": settings.user_agent,
            },
            transport=transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._closed = False

    @property
    def settings(self) -> FredSettings:
        return self._settings

    def build_params(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Merge caller params with api_key and file_type=json."""
        merged: dict[str, Any] = {"file_type": "json", "api_key": self._api_key}
        if params:
            for key, value in params.items():
                if key.lower() in {"api_key", "apikey", "token"}:
                    continue
                if value is not None:
                    merged[key] = value
        return merged

    def sanitized_request_url(self, path: str, params: dict[str, Any]) -> str:
        """Absolute URL with credentials stripped (for logs / source refs)."""
        query = urlencode(
            [
                (k, v)
                for k, v in params.items()
                if str(k).lower() not in {"api_key", "apikey", "token"}
            ]
        )
        base = self._settings.base_url.rstrip("/")
        raw = f"{base}{path}?{query}" if query else f"{base}{path}"
        return sanitize_url(raw)

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        safe_params = self.build_params(params)
        sanitized = self.sanitized_request_url(path, safe_params)

        async def _op() -> httpx.Response:
            return await self._client.get(path, params=safe_params)

        logger.debug(
            "fred http get",
            extra=structured_extra(
                event="fred.http.get",
                source="fred_http",
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
