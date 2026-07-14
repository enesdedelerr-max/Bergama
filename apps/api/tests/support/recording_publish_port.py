"""Test-only RecordingPublishPort for orchestrator suites (#305).

Not part of the application runtime surface.
"""

from __future__ import annotations

from app.core.clock import Clock
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.ports import PublishResult


class RecordingPublishPort:
    """Test sink that records successful live publishes."""

    def __init__(self, *, clock: Clock | None = None, fail_next: bool = False) -> None:
        self._clock = clock
        self._fail_next = fail_next
        self.published: list[tuple[CanonicalMarketEvent, str, PipelineContext]] = []

    def set_fail_next(self, value: bool = True) -> None:
        self._fail_next = value

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult:
        if self._fail_next:
            self._fail_next = False
            return PublishResult(ok=False, published_at=None, detail="forced failure")
        published_at = self._clock.now() if self._clock is not None else context.received_at
        self.published.append((event, routing_key, context))
        return PublishResult(ok=True, published_at=published_at, detail="recorded")
