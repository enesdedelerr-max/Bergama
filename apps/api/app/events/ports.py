"""Application-owned event transport ports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.events.envelope import EventEnvelope
from app.events.errors import EventProcessingError
from app.events.topics import KafkaTopic


@dataclass(frozen=True, slots=True)
class PublishResult:
    topic: str
    partition: int
    offset: int
    timestamp: datetime | None


@dataclass(frozen=True, slots=True)
class ConsumedEvent:
    envelope: EventEnvelope
    topic: str
    partition: int
    offset: int
    timestamp: datetime | None
    key: str | bytes | None
    headers: dict[str, str]


class EventProducer(Protocol):
    async def start(self) -> None: ...

    async def publish(
        self,
        topic: KafkaTopic,
        event: EventEnvelope,
        *,
        key: str | bytes | None = None,
    ) -> PublishResult: ...

    async def stop(self) -> None: ...


class EventConsumer(Protocol):
    async def start(self) -> None: ...

    async def get(self) -> ConsumedEvent: ...

    async def commit(self, event: ConsumedEvent) -> None: ...

    async def stop(self) -> None: ...


class EventHandler(Protocol):
    async def handle(self, event: EventEnvelope) -> None: ...


class DlqPublisher(Protocol):
    async def publish_failed(
        self,
        consumed_event: ConsumedEvent,
        error: EventProcessingError,
        attempts: int,
    ) -> None: ...
