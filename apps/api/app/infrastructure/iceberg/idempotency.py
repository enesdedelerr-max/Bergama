"""Bounded process-local committed-key index (#307).

Suppresses observable re-appends only for the lifetime of the process.
Not durable across restarts. Not exactly-once.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.clock import Clock


@dataclass(slots=True)
class _Entry:
    committed_at: datetime


class CommittedKeyIndex:
    """TTL + max-entry bounded index of successfully committed idempotency keys."""

    def __init__(
        self,
        *,
        clock: Clock,
        ttl_seconds: float,
        max_entries: int,
    ) -> None:
        if ttl_seconds <= 0:
            msg = "ttl_seconds must be > 0"
            raise ValueError(msg)
        if max_entries <= 0:
            msg = "max_entries must be > 0"
            raise ValueError(msg)
        self._clock = clock
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_entries = max_entries
        self._entries: OrderedDict[str, _Entry] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def contains(self, key: str) -> bool:
        self._evict_expired()
        return key in self._entries

    def add_many(self, keys: list[str]) -> None:
        """Record keys after successful Iceberg snapshots + Kafka offset commit."""
        now = self._clock.now()
        self._evict_expired(now=now)
        for key in keys:
            if key in self._entries:
                del self._entries[key]
            self._entries[key] = _Entry(committed_at=now)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def _evict_expired(self, *, now: datetime | None = None) -> None:
        moment = now if now is not None else self._clock.now()
        expired = [
            key for key, entry in self._entries.items() if moment - entry.committed_at >= self._ttl
        ]
        for key in expired:
            del self._entries[key]
