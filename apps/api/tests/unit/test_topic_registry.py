"""Unit tests for topic registry."""

from __future__ import annotations

import pytest
from app.events.topics import KafkaTopic, TopicRegistry


def test_topic_registry_resolution() -> None:
    registry = TopicRegistry()
    assert registry.resolve(KafkaTopic.EVENTS) == "events"
    assert registry.resolve(KafkaTopic.MARKET_DATA) == "market-data"


def test_topic_prefix_behavior() -> None:
    registry = TopicRegistry(topic_prefix="dev.")
    assert registry.resolve(KafkaTopic.AUDIT) == "dev.audit"


def test_invalid_topic_name_rejected() -> None:
    with pytest.raises(ValueError, match="unknown kafka topic"):
        TopicRegistry().resolve("not-a-real-topic")


def test_invalid_prefix_rejected() -> None:
    with pytest.raises(ValueError, match="invalid topic prefix"):
        TopicRegistry(topic_prefix="Bad Prefix!")
