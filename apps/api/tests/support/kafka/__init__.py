"""Test-only Kafka event runtime support (Issue #208B).

Never import from production application wiring.
"""

from __future__ import annotations

from tests.support.kafka.broker import BrokerRecord, InMemoryEventBroker
from tests.support.kafka.consumer import FakeEventConsumer
from tests.support.kafka.dlq import CapturedDlqFailure, FakeDlqPublisher
from tests.support.kafka.fixtures import EventRuntimeHarness, event_runtime_harness
from tests.support.kafka.producer import FakeEventProducer

__all__ = [
    "BrokerRecord",
    "CapturedDlqFailure",
    "EventRuntimeHarness",
    "FakeDlqPublisher",
    "FakeEventConsumer",
    "FakeEventProducer",
    "InMemoryEventBroker",
    "event_runtime_harness",
]
