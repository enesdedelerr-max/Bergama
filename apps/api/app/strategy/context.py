"""Strategy evaluation context."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.clock import Clock
from app.strategy.identity import StrategyIdentity


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Injected deterministic context for one strategy instance/session."""

    identity: StrategyIdentity
    run_id: str
    session_id: str
    clock: Clock
    configuration_fingerprint: str
    correlation_id: str | None = None
    causation_id: str | None = None
