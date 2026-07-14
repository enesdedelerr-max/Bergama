"""Bounded in-flight admission control (#305).

This is not a durable buffer or asynchronous work queue. Capacity is the
maximum number of events concurrently past admission into publish.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


class AdmissionTimeoutError(RuntimeError):
    """Raised when in-flight capacity cannot be acquired within the timeout."""


@dataclass(frozen=True, slots=True)
class AdmissionStats:
    max_in_flight: int
    in_flight: int
    overflow_count: int


class InFlightAdmissionController:
    """Semaphore-backed bounded in-flight admission control."""

    def __init__(self, *, max_in_flight: int, timeout_seconds: float) -> None:
        if max_in_flight < 1:
            msg = "max_in_flight must be >= 1"
            raise ValueError(msg)
        if timeout_seconds <= 0:
            msg = "admission_timeout_seconds must be > 0"
            raise ValueError(msg)
        self._max_in_flight = max_in_flight
        self._timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_in_flight)
        self._in_flight = 0
        self._overflow_count = 0
        self._lock = asyncio.Lock()

    @property
    def max_in_flight(self) -> int:
        return self._max_in_flight

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    def stats(self) -> AdmissionStats:
        return AdmissionStats(
            max_in_flight=self._max_in_flight,
            in_flight=self._in_flight,
            overflow_count=self._overflow_count,
        )

    async def acquire(self) -> None:
        """Acquire one in-flight slot or raise AdmissionTimeoutError."""
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._timeout_seconds)
        except TimeoutError as exc:
            async with self._lock:
                self._overflow_count += 1
            msg = (
                f"admission timeout after {self._timeout_seconds}s "
                f"(max_in_flight={self._max_in_flight})"
            )
            raise AdmissionTimeoutError(msg) from exc
        async with self._lock:
            self._in_flight += 1

    def release(self) -> None:
        """Release one in-flight slot. Safe after a successful acquire only."""
        self._semaphore.release()
        # Keep counter non-negative under misuse; acquire always pairs with release.
        self._in_flight = max(0, self._in_flight - 1)

    def clear(self) -> None:
        """Reset counters for shutdown. Does not recreate the semaphore."""
        self._overflow_count = 0
        self._in_flight = 0
