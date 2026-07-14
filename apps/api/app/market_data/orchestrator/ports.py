"""PublishPort protocol without Kafka or EventEnvelope (#305).

Infrastructure-neutral sink boundary. ``ok=True`` is valid only for a successful
live delivery that the orchestrator may map to ``PipelineDecision.PUBLISHED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.core.clock import Clock
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext

PublishMode = Literal["live", "dry_run"]


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Outcome of a PublishPort invocation.

    Rules:
    - ``ok=True`` only for successful live delivery.
    - Dry-run must use ``mode=\"dry_run\"`` and ``ok=False``.
    - Failures use ``ok=False`` and ``mode=\"live\"``.
    """

    ok: bool
    published_at: datetime | None
    detail: str | None = None
    mode: PublishMode = "live"

    def __post_init__(self) -> None:
        if self.mode == "dry_run" and self.ok:
            msg = "dry_run PublishResult must not set ok=True"
            raise ValueError(msg)
        if self.ok and self.mode != "live":
            msg = "ok=True requires mode='live'"
            raise ValueError(msg)


class PublishPort(Protocol):
    """Sink boundary for admitted canonical events."""

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult: ...


class DryRunPublishPort:
    """Explicit diagnostic sink — never reports a successful live publish."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock
        self.invocations: list[tuple[CanonicalMarketEvent, str, PipelineContext]] = []

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult:
        observed_at = self._clock.now() if self._clock is not None else context.received_at
        self.invocations.append((event, routing_key, context))
        return PublishResult(
            ok=False,
            published_at=observed_at,
            detail="dry_run",
            mode="dry_run",
        )


# Explicit alias for diagnostics/tests — never an implicit production default.
NoOpPublishPort = DryRunPublishPort
