"""Application-level SEC request spacing (Issue #304C)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic

AsyncSleeper = Callable[[float], Awaitable[None]]


async def default_sleeper(seconds: float) -> None:
    await asyncio.sleep(seconds)


class MinIntervalRateLimiter:
    """Serialize requests with a fixed minimum spacing (no bursts)."""

    def __init__(
        self,
        *,
        min_interval_seconds: float,
        sleeper: AsyncSleeper = default_sleeper,
        monotonic_fn: Callable[[], float] = monotonic,
    ) -> None:
        if min_interval_seconds < 0:
            msg = "min_interval_seconds must be >= 0"
            raise ValueError(msg)
        self._min_interval = min_interval_seconds
        self._sleeper = sleeper
        self._monotonic = monotonic_fn
        self._lock = asyncio.Lock()
        self._last_request_at: float | None = None

    async def acquire(self) -> None:
        async with self._lock:
            now = self._monotonic()
            if self._last_request_at is not None:
                elapsed = now - self._last_request_at
                wait = self._min_interval - elapsed
                if wait > 0:
                    await self._sleeper(wait)
                    now = self._monotonic()
            self._last_request_at = now
