"""Typed topic registry."""

from __future__ import annotations

import re
from enum import StrEnum

_TOPIC_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_PREFIX_PATTERN = re.compile(r"^[a-z0-9._-]*$")


class KafkaTopic(StrEnum):
    """Canonical Sprint 1 / Sprint 2 topic identifiers."""

    MARKET_DATA = "market-data"
    EVENTS = "events"
    AUDIT = "audit"
    EXECUTION = "execution"
    RISK = "risk"


class TopicRegistry:
    """Resolves symbolic topics to broker topic names with optional prefix."""

    def __init__(self, *, topic_prefix: str = "") -> None:
        prefix = topic_prefix.strip()
        if not _PREFIX_PATTERN.fullmatch(prefix):
            msg = f"invalid topic prefix {prefix!r}"
            raise ValueError(msg)
        self._prefix = prefix

    def resolve(self, topic: KafkaTopic | str) -> str:
        """Return the broker topic name for a symbolic topic."""
        if isinstance(topic, KafkaTopic):
            base = topic.value
        else:
            try:
                base = KafkaTopic(topic).value
            except ValueError as exc:
                msg = f"unknown kafka topic {topic!r}"
                raise ValueError(msg) from exc
        name = f"{self._prefix}{base}" if self._prefix else base
        if not _TOPIC_PATTERN.fullmatch(name):
            msg = f"invalid kafka topic name {name!r}"
            raise ValueError(msg)
        return name

    def resolve_many(self, topics: list[KafkaTopic | str]) -> list[str]:
        return [self.resolve(topic) for topic in topics]
