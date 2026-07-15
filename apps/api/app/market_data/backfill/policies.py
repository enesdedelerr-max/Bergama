"""Backfill policy helpers (#309)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.core.backfill_settings import BackfillSettings
from app.market_data.backfill.errors import BackfillBackpressureTimeoutError, BackfillCancelledError
from app.market_data.backfill.models import BackfillMode, BackfillRequest, validate_backfill_request
from app.market_data.backfill.ports import BackfillSleeper


@dataclass(frozen=True, slots=True)
class ResolvedBackfillLimits:
    batch_size: int
    max_in_flight_events: int
    events_per_second: float | None
    max_concurrent_slices: int
    slice_retry_limit: int


def resolve_limits(request: BackfillRequest, settings: BackfillSettings) -> ResolvedBackfillLimits:
    validate_backfill_request(request, settings)
    batch = request.batch_size if request.batch_size is not None else settings.default_batch_size
    inflight = (
        request.max_in_flight_events
        if request.max_in_flight_events is not None
        else settings.max_in_flight_events
    )
    rate = (
        request.events_per_second
        if request.events_per_second is not None
        else settings.default_events_per_second
    )
    return ResolvedBackfillLimits(
        batch_size=batch,
        max_in_flight_events=min(inflight, batch),
        events_per_second=rate,
        max_concurrent_slices=1,  # MVP sequential for all providers
        slice_retry_limit=settings.slice_retry_limit,
    )


def sink_type_for_mode(mode: BackfillMode) -> str:
    return "publish_port" if mode is BackfillMode.PUBLISH else "none"


class AsyncioBackfillSleeper:
    async def sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        await asyncio.sleep(seconds)


class NoOpBackfillSleeper:
    async def sleep(self, seconds: float) -> None:
        _ = seconds


class TokenBucketRateLimiter:
    def __init__(
        self,
        *,
        events_per_second: float | None,
        sleeper: BackfillSleeper,
        admission_timeout_seconds: float = 30.0,
    ) -> None:
        self._rate = events_per_second
        self._sleeper = sleeper
        self._timeout = admission_timeout_seconds
        self._interval = (1.0 / events_per_second) if events_per_second else None
        self._last_admit_mono: float | None = None

    async def admit(self, *, cancelled: bool) -> None:
        if cancelled:
            raise BackfillCancelledError(detail="cancelled before rate admit")
        if self._interval is None:
            return
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self._last_admit_mono is None:
            self._last_admit_mono = now
            return
        delay = self._last_admit_mono + self._interval - now
        if delay <= 0:
            self._last_admit_mono = now
            return
        if delay > self._timeout:
            raise BackfillBackpressureTimeoutError(detail="rate limiter admission timeout")
        await self._sleeper.sleep(delay)
        if cancelled:
            raise BackfillCancelledError(detail="cancelled during rate wait")
        self._last_admit_mono = asyncio.get_running_loop().time()
