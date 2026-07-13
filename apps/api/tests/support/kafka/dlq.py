"""Test-only DlqPublisher."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.events.errors import DlqUnavailableError, EventProcessingError
from app.events.ports import ConsumedEvent
from app.events.serialization import serialize_event


@dataclass(frozen=True, slots=True)
class CapturedDlqFailure:
    topic: str
    partition: int
    offset: int
    event_bytes: bytes
    error_code: str
    attempts: int


@dataclass
class FakeDlqPublisher:
    """Stores failed records for assertions; can be configured to fail."""

    fail: bool = False
    failures: list[CapturedDlqFailure] = field(default_factory=list)

    async def publish_failed(
        self,
        consumed_event: ConsumedEvent,
        error: EventProcessingError,
        attempts: int,
    ) -> None:
        if self.fail:
            raise DlqUnavailableError("fake DLQ unavailable")
        self.failures.append(
            CapturedDlqFailure(
                topic=consumed_event.topic,
                partition=consumed_event.partition,
                offset=consumed_event.offset,
                event_bytes=serialize_event(consumed_event.envelope),
                error_code=error.code,
                attempts=attempts,
            )
        )
