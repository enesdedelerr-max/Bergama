"""Bounded reconnect backoff for Polygon WebSocket sessions."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

AsyncSleeper = Callable[[float], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class WebsocketReconnectPolicy:
    max_attempts: int = 5
    initial_delay_seconds: float = 0.25
    max_delay_seconds: float = 8.0
    multiplier: float = 2.0

    def delay_for_attempt(self, attempt: int) -> float:
        # attempt is 1-based for the first reconnect sleep.
        delay = self.initial_delay_seconds * (self.multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)


async def default_sleeper(seconds: float) -> None:
    await asyncio.sleep(seconds)
