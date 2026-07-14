"""Per-stream sequencing for the market-data orchestrator (#305).

Guarantees:
- Scope is ``(instrument_key, event_type)``.
- Same-stream submissions are serialized via a keyed asyncio lock so
  concurrent coroutines on one stream cannot interleave publish work.
- Different streams do not block each other.
- Timestamps are never globally sorted or repaired; late/out-of-order
  ``occurred_at`` values are flagged only.
- This is **not** global or event-time ordering / watermarking.

Active stream state is bounded (``_MAX_IDLE_STREAMS``) with deterministic
eviction of idle streams.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime

from app.market_data.envelope import CanonicalMarketEvent

_MAX_IDLE_STREAMS = 10_000


@dataclass(frozen=True, slots=True)
class StreamSequenceInfo:
    """Observable sequencing annotation for one event on a stream."""

    stream_key: str
    sequence: int
    out_of_order: bool


@dataclass(slots=True)
class _StreamState:
    lock: asyncio.Lock
    sequence: int
    last_occurred: datetime | None
    waiters: int


class StreamLease:
    """Held per-stream lock lease — must be released on every exit path."""

    def __init__(
        self,
        sequencer: PerStreamSequencer,
        info: StreamSequenceInfo,
    ) -> None:
        self._sequencer = sequencer
        self.info = info
        self._released = False

    async def release(self) -> None:
        if self._released:
            return
        self._released = True
        await self._sequencer.release(self.info.stream_key)


class PerStreamSequencer:
    """Keyed async serialization + monotonic sequence numbers per stream."""

    def __init__(self, *, max_idle_streams: int = _MAX_IDLE_STREAMS) -> None:
        if max_idle_streams < 1:
            msg = "max_idle_streams must be >= 1"
            raise ValueError(msg)
        self._max_idle_streams = max_idle_streams
        self._streams: OrderedDict[str, _StreamState] = OrderedDict()
        self._meta_lock = asyncio.Lock()

    def __len__(self) -> int:
        return len(self._streams)

    def clear(self) -> None:
        self._streams.clear()

    @staticmethod
    def stream_key_for(event: CanonicalMarketEvent) -> str:
        return f"{event.instrument.instrument_key}|{event.event_type.value}"

    async def acquire(self, event: CanonicalMarketEvent) -> StreamLease:
        """Serialize this stream and assign the next sequence number."""
        key = self.stream_key_for(event)
        async with self._meta_lock:
            state = self._streams.get(key)
            if state is None:
                self._evict_idle_locked(reserving=1)
                state = _StreamState(
                    lock=asyncio.Lock(),
                    sequence=0,
                    last_occurred=None,
                    waiters=0,
                )
                self._streams[key] = state
            state.waiters += 1
            self._streams.move_to_end(key)
            lock = state.lock

        try:
            await lock.acquire()
        except asyncio.CancelledError:
            await self._abandon_wait(key, release_lock=False)
            raise

        try:
            async with self._meta_lock:
                state = self._streams[key]
                previous = state.last_occurred
                out_of_order = previous is not None and event.occurred_at < previous
                state.sequence += 1
                if previous is None or event.occurred_at >= previous:
                    state.last_occurred = event.occurred_at
                info = StreamSequenceInfo(
                    stream_key=key,
                    sequence=state.sequence,
                    out_of_order=out_of_order,
                )
            return StreamLease(self, info)
        except BaseException:
            await self._abandon_wait(key, release_lock=True)
            raise

    async def _abandon_wait(self, stream_key: str, *, release_lock: bool) -> None:
        """Drop waiter accounting; optionally release a lock acquired before failure."""
        async with self._meta_lock:
            state = self._streams.get(stream_key)
            if state is None:
                return
            if release_lock and state.lock.locked():
                state.lock.release()
            state.waiters = max(0, state.waiters - 1)
            self._streams.move_to_end(stream_key)
            if state.waiters == 0 and not state.lock.locked():
                self._evict_idle_locked(reserving=0)

    async def release(self, stream_key: str) -> None:
        async with self._meta_lock:
            state = self._streams.get(stream_key)
            if state is None:
                return
            if state.lock.locked():
                state.lock.release()
            state.waiters = max(0, state.waiters - 1)
            self._streams.move_to_end(stream_key)
            if state.waiters == 0:
                self._evict_idle_locked(reserving=0)

    def _evict_idle_locked(self, *, reserving: int) -> None:
        """Drop oldest idle streams when above the bound (deterministic LRU)."""
        while len(self._streams) + reserving > self._max_idle_streams:
            victim_key: str | None = None
            for key, state in self._streams.items():
                if state.waiters == 0 and not state.lock.locked():
                    victim_key = key
                    break
            if victim_key is None:
                break
            del self._streams[victim_key]


# Compatibility aliases while callers migrate from the old naming.
OrderingDecision = StreamSequenceInfo
OrderingTracker = PerStreamSequencer
