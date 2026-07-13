"""Narrow clock abstraction for deterministic token timestamps."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Timezone-aware clock used by token issuance/validation helpers."""

    def now(self) -> datetime:
        """Return the current UTC-aware datetime."""
        ...


class SystemClock:
    """Production wall-clock implementation (UTC)."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Deterministic clock for tests."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            msg = "FixedClock requires a timezone-aware datetime"
            raise ValueError(msg)
        self._instant = instant.astimezone(UTC)

    def now(self) -> datetime:
        return self._instant
