"""Bounded TTL dedup store with reserve → commit / release (#305)."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class DedupEntryState(StrEnum):
    RESERVED = "reserved"
    COMMITTED = "committed"


class DedupReserveOutcome(StrEnum):
    RESERVED = "reserved"
    DUPLICATE = "duplicate"
    SKIPPED_REVISION = "skipped_revision"
    CAPACITY_EXHAUSTED = "capacity_exhausted"


@dataclass(frozen=True, slots=True)
class DedupEntry:
    state: DedupEntryState
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class DedupReserveResult:
    outcome: DedupReserveOutcome
    key: str
    existing_state: DedupEntryState | None = None


class BoundedDedupStore:
    """In-memory dedup with reserved/committed states, TTL, and max-entry bounds.

    Lifecycle for non-revisions:
    1. ``try_reserve`` — atomic check/insert as RESERVED
    2. On successful delivery — ``commit``
    3. On failed / dry-run delivery — ``release``

    Revisions skip reservation so they are never suppressed as the original.
    """

    def __init__(self, *, ttl: timedelta, max_entries: int) -> None:
        if ttl.total_seconds() <= 0:
            msg = "dedup TTL must be positive"
            raise ValueError(msg)
        if max_entries < 1:
            msg = "max_entries must be >= 1"
            raise ValueError(msg)
        self._ttl = ttl
        self._max_entries = max_entries
        self._entries: OrderedDict[str, DedupEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def purge_expired(self, *, now: datetime) -> int:
        cutoff = now - self._ttl
        removed = 0
        stale = [key for key, entry in self._entries.items() if entry.timestamp < cutoff]
        for key in stale:
            del self._entries[key]
            removed += 1
        return removed

    def _evict_oldest_committed(self) -> bool:
        """Deterministically evict the oldest committed entry. Returns True if evicted."""
        for key, entry in self._entries.items():
            if entry.state is DedupEntryState.COMMITTED:
                del self._entries[key]
                return True
        return False

    def _ensure_capacity(self) -> bool:
        """Make space for one new entry. Evict committed only. Fail if still full."""
        while len(self._entries) >= self._max_entries:
            if not self._evict_oldest_committed():
                return False
        return True

    async def try_reserve(
        self,
        key: str,
        *,
        now: datetime,
        is_revision: bool,
    ) -> DedupReserveResult:
        async with self._lock:
            self.purge_expired(now=now)
            if is_revision:
                return DedupReserveResult(
                    outcome=DedupReserveOutcome.SKIPPED_REVISION,
                    key=key,
                )
            existing = self._entries.get(key)
            if existing is not None:
                self._entries.move_to_end(key)
                return DedupReserveResult(
                    outcome=DedupReserveOutcome.DUPLICATE,
                    key=key,
                    existing_state=existing.state,
                )
            if not self._ensure_capacity():
                return DedupReserveResult(
                    outcome=DedupReserveOutcome.CAPACITY_EXHAUSTED,
                    key=key,
                )
            self._entries[key] = DedupEntry(state=DedupEntryState.RESERVED, timestamp=now)
            return DedupReserveResult(outcome=DedupReserveOutcome.RESERVED, key=key)

    async def commit(self, key: str, *, now: datetime) -> None:
        async with self._lock:
            self.purge_expired(now=now)
            entry = self._entries.get(key)
            if entry is None:
                # Prefer persisting a successful delivery over unbounded growth.
                if not self._ensure_capacity() and self._entries:
                    oldest_key = next(iter(self._entries))
                    del self._entries[oldest_key]
                self._entries[key] = DedupEntry(
                    state=DedupEntryState.COMMITTED,
                    timestamp=now,
                )
                return
            self._entries[key] = DedupEntry(state=DedupEntryState.COMMITTED, timestamp=now)
            self._entries.move_to_end(key)

    async def release(self, key: str) -> None:
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return
            if entry.state is DedupEntryState.RESERVED:
                del self._entries[key]
