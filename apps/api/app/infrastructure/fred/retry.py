"""HTTP retry helper for FRED REST (Issue #304B)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Protocol, TypeVar

import httpx

from app.infrastructure.fred.errors import (
    FredConnectionFailedError,
    FredProviderError,
    FredRateLimitedError,
    FredTimeoutError,
)

T = TypeVar("T")
AsyncSleeper = Callable[[float], Awaitable[None]]

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class FailurePolicy(Protocol):
    """Thin policy surface used by FRED HTTP retries."""

    def should_retry_status(self, status_code: int) -> bool: ...

    def delay_for_attempt(self, attempt: int) -> float: ...

    def delay_from_retry_after(self, header: str | None) -> float | None: ...


@dataclass(frozen=True, slots=True)
class FredHttpRetryPolicy:
    """Bounded exponential backoff; honors Retry-After when valid."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.25
    max_delay_seconds: float = 8.0
    multiplier: float = 2.0
    retry_after_max_seconds: float = 30.0

    def should_retry_status(self, status_code: int) -> bool:
        return status_code in _RETRYABLE_STATUS

    def delay_for_attempt(self, attempt: int) -> float:
        delay = self.initial_delay_seconds * (self.multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)

    def delay_from_retry_after(self, header: str | None) -> float | None:
        if header is None:
            return None
        text = header.strip()
        if not text:
            return None
        try:
            seconds = float(text)
            if seconds < 0:
                return None
            return min(seconds, self.retry_after_max_seconds)
        except ValueError:
            pass
        try:
            when = parsedate_to_datetime(text)
            if when.tzinfo is None:
                return None
            import datetime as dt

            delta = (when - dt.datetime.now(dt.UTC)).total_seconds()
            if delta < 0:
                return 0.0
            return min(delta, self.retry_after_max_seconds)
        except (TypeError, ValueError, OverflowError, IndexError):
            return None


async def default_sleeper(seconds: float) -> None:
    await asyncio.sleep(seconds)


async def request_with_retries(
    *,
    operation: Callable[[], Awaitable[httpx.Response]],
    policy: FailurePolicy,
    max_attempts: int,
    sleeper: AsyncSleeper = default_sleeper,
) -> httpx.Response:
    """Execute an HTTP call with bounded retries for transient failures."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await operation()
        except httpx.TimeoutException as exc:
            last_error = FredTimeoutError("fred request timed out")
            if attempt >= max_attempts:
                raise last_error from exc
            await sleeper(policy.delay_for_attempt(attempt))
            continue
        except httpx.TransportError as exc:
            last_error = FredConnectionFailedError("fred connection failed")
            if attempt >= max_attempts:
                raise last_error from exc
            await sleeper(policy.delay_for_attempt(attempt))
            continue

        if not policy.should_retry_status(response.status_code):
            return response

        if attempt >= max_attempts:
            if response.status_code == 429:
                raise FredRateLimitedError("fred rate limited")
            raise FredProviderError(f"fred provider error status={response.status_code}")

        retry_after = policy.delay_from_retry_after(response.headers.get("Retry-After"))
        delay = retry_after if retry_after is not None else policy.delay_for_attempt(attempt)
        await sleeper(delay)

    if last_error is not None:
        raise last_error
    raise FredProviderError("fred request failed without response")
