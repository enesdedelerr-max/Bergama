"""PublishPort protocol without Kafka or EventEnvelope (#305).

Infrastructure-neutral sink boundary. Successful delivery is represented only
by ``PublishResult.succeeded=True``. Dry-run never returns a successful result.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.core.clock import Clock
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Infrastructure-neutral publish outcome.

    Allowed fields only:
    - succeeded
    - published_at
    - sink_message_id (optional)
    - idempotency_acknowledged
    - safe_metadata (string map, no secrets/payloads)
    """

    succeeded: bool
    published_at: datetime | None
    sink_message_id: str | None = None
    idempotency_acknowledged: bool = False
    safe_metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Freeze metadata as a plain dict for immutability callers rely on.
        object.__setattr__(self, "safe_metadata", dict(self.safe_metadata))
        for key, value in self.safe_metadata.items():
            lowered = key.lower()
            forbidden = ("password", "secret", "token", "api_key", "authorization")
            if any(token in lowered for token in forbidden):
                msg = f"forbidden safe_metadata key {key!r}"
                raise ValueError(msg)
            if not isinstance(value, str):
                msg = "safe_metadata values must be strings"
                raise TypeError(msg)


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
    """Diagnostic sink used only when orchestrator dry_run=true.

    Never returns ``succeeded=True``. The orchestrator maps dry-run config to
    ``PipelineDecision.DRY_RUN`` and must not treat this as a live publish.
    """

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
            succeeded=False,
            published_at=observed_at,
            sink_message_id=None,
            idempotency_acknowledged=False,
            safe_metadata={"dry_run": "true"},
        )


NoOpPublishPort = DryRunPublishPort
