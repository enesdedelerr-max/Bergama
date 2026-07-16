"""Bounded process-local Portfolio metrics."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class PortfolioMetrics:
    mutations_evaluated: int = 0
    fills_applied: int = 0
    cash_adjustments: int = 0
    mark_updates: int = 0
    duplicates: int = 0
    positions_opened: int = 0
    positions_closed: int = 0
    reversals: int = 0
    version_conflicts: int = 0
    repository_failures: int = 0
    accounting_failures: int = 0
    latency_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    errors_by_code: Counter[str] = field(default_factory=Counter)

    def observe_latency(self, milliseconds: float) -> None:
        self.latency_ms.append(milliseconds)

    def record_error(self, code: str) -> None:
        self.errors_by_code[code] += 1
