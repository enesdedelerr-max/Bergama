"""Deterministic clocks for contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.clock import FixedClock

# Far enough in the future relative to synthetic provider timestamps
# so PIT ordering (occurred_at <= known_at <= ingested_at) holds.
OBSERVED_AT = datetime(2024, 6, 15, 16, 0, 0, tzinfo=UTC)


def observed_clock() -> FixedClock:
    return FixedClock(OBSERVED_AT)
