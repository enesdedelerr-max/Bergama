"""Bounded in-memory retry policy for consumer workers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

AsyncSleeper = Callable[[float], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Deterministic exponential backoff without jitter."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.05
    max_delay_seconds: float = 1.0
    multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            msg = "max_attempts must be >= 1"
            raise ValueError(msg)
        if self.initial_delay_seconds < 0 or self.max_delay_seconds < 0:
            msg = "delays must be >= 0"
            raise ValueError(msg)
        if self.multiplier < 1:
            msg = "multiplier must be >= 1"
            raise ValueError(msg)

    def delay_for_attempt(self, attempt: int) -> float:
        """Return delay after a failed attempt (1-based attempt that just failed)."""
        if attempt < 1:
            msg = "attempt must be >= 1"
            raise ValueError(msg)
        delay = self.initial_delay_seconds * (self.multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)

    def delays(self) -> list[float]:
        """Delays between attempts (length max_attempts - 1)."""
        return [self.delay_for_attempt(i) for i in range(1, self.max_attempts)]
