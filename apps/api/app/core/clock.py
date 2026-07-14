"""Narrow clock and JTI abstractions for deterministic token timestamps."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


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


class JtiGenerator(Protocol):
    """Produces JWT ``jti`` claim values."""

    def __call__(self) -> str:
        """Return the next token ID."""
        ...


class UuidJtiGenerator:
    """Production JTI generator using UUID4."""

    def __call__(self) -> str:
        return str(uuid4())


class FixedJtiGenerator:
    """Deterministic JTI generator for tests."""

    def __init__(self, value: str) -> None:
        if not value.strip():
            msg = "JTI value must be non-empty"
            raise ValueError(msg)
        self._value = value

    def __call__(self) -> str:
        return self._value
