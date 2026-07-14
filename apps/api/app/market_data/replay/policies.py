"""Replay policy helpers (#308)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.core.replay_settings import ReplaySettings
from app.market_data.replay.errors import ReplayBackpressureTimeoutError, ReplayCancelledError
from app.market_data.replay.models import ReplayMode, ReplayRequest, validate_replay_request
from app.market_data.replay.ports import ReplaySleeper


@dataclass(frozen=True, slots=True)
class ResolvedReplayLimits:
    batch_size: int
    max_in_flight: int
    events_per_second: float | None


def resolve_limits(request: ReplayRequest, settings: ReplaySettings) -> ResolvedReplayLimits:
    validate_replay_request(request, settings)
    batch = request.batch_size if request.batch_size is not None else settings.default_batch_size
    inflight = (
        request.max_in_flight
        if request.max_in_flight is not None
        else settings.default_max_in_flight
    )
    rate = (
        request.events_per_second
        if request.events_per_second is not None
        else settings.default_events_per_second
    )
    return ResolvedReplayLimits(
        batch_size=batch,
        max_in_flight=min(inflight, batch),
        events_per_second=rate,
    )


def sink_type_for_mode(mode: ReplayMode) -> str:
    if mode is ReplayMode.REPUBLISH:
        return "publish_port"
    if mode is ReplayMode.CUSTOM_SINK:
        return "custom_sink"
    return "none"


class AsyncioReplaySleeper:
    """Production sleeper using asyncio.sleep."""

    async def sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        await asyncio.sleep(seconds)


class NoOpReplaySleeper:
    """Test sleeper — never sleeps."""

    async def sleep(self, seconds: float) -> None:
        _ = seconds


class TokenBucketRateLimiter:
    """Simple sequential rate limiter. No unbounded queue. Cancellation-safe."""

    def __init__(
        self,
        *,
        events_per_second: float | None,
        sleeper: ReplaySleeper,
        admission_timeout_seconds: float = 30.0,
    ) -> None:
        self._rate = events_per_second
        self._sleeper = sleeper
        self._timeout = admission_timeout_seconds
        self._interval = (1.0 / events_per_second) if events_per_second else None
        self._last_admit_mono: float | None = None

    async def admit(self, *, cancelled: bool) -> None:
        if cancelled:
            raise ReplayCancelledError(detail="cancelled before rate admit")
        if self._interval is None:
            return
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self._last_admit_mono is None:
            self._last_admit_mono = now
            return
        due = self._last_admit_mono + self._interval
        delay = due - now
        if delay <= 0:
            self._last_admit_mono = now
            return
        if delay > self._timeout:
            raise ReplayBackpressureTimeoutError(detail="rate limiter admission timeout")
        await self._sleeper.sleep(delay)
        if cancelled:
            raise ReplayCancelledError(detail="cancelled during rate wait")
        self._last_admit_mono = asyncio.get_running_loop().time()
