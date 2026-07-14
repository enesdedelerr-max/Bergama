"""Per-(instrument, event_type) ordering tracker (#305).

Never globally sorts. Detects out-of-order by occurred_at within a scope
without reordering the stream.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.market_data.envelope import CanonicalMarketEvent


@dataclass(frozen=True, slots=True)
class OrderingDecision:
    scope: str
    sequence: int
    out_of_order: bool


class OrderingTracker:
    """Assigns monotonic sequence numbers per ordering scope."""

    def __init__(self) -> None:
        self._sequences: dict[str, int] = {}
        self._last_occurred: dict[str, datetime] = {}

    def clear(self) -> None:
        self._sequences.clear()
        self._last_occurred.clear()

    @staticmethod
    def scope_for(event: CanonicalMarketEvent) -> str:
        return f"{event.instrument.instrument_key}|{event.event_type.value}"

    def observe(self, event: CanonicalMarketEvent) -> OrderingDecision:
        scope = self.scope_for(event)
        previous = self._last_occurred.get(scope)
        out_of_order = previous is not None and event.occurred_at < previous
        sequence = self._sequences.get(scope, 0) + 1
        self._sequences[scope] = sequence
        # Advance watermark only when not regressing; preserve first watermark
        # so subsequent events still compare against the highest seen occurred_at.
        if previous is None or event.occurred_at >= previous:
            self._last_occurred[scope] = event.occurred_at
        return OrderingDecision(scope=scope, sequence=sequence, out_of_order=out_of_order)
