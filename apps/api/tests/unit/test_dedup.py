"""Unit tests for reserve/commit/release dedup store (#305)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.market_data.orchestrator.dedup import (
    BoundedDedupStore,
    DedupEntryState,
    DedupReserveOutcome,
)


@pytest.mark.asyncio
async def test_reserve_commit_suppresses_replay() -> None:
    store = BoundedDedupStore(ttl=timedelta(seconds=60), max_entries=10)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    first = await store.try_reserve("a", now=t0, is_revision=False)
    assert first.outcome is DedupReserveOutcome.RESERVED
    await store.commit("a", now=t0)
    second = await store.try_reserve("a", now=t0 + timedelta(seconds=1), is_revision=False)
    assert second.outcome is DedupReserveOutcome.DUPLICATE
    assert second.existing_state is DedupEntryState.COMMITTED


@pytest.mark.asyncio
async def test_release_after_failure_allows_replay() -> None:
    store = BoundedDedupStore(ttl=timedelta(seconds=60), max_entries=10)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    await store.try_reserve("a", now=t0, is_revision=False)
    await store.release("a")
    again = await store.try_reserve("a", now=t0 + timedelta(seconds=1), is_revision=False)
    assert again.outcome is DedupReserveOutcome.RESERVED


@pytest.mark.asyncio
async def test_reserved_key_suppresses_concurrent_duplicate() -> None:
    store = BoundedDedupStore(ttl=timedelta(seconds=60), max_entries=10)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    first = await store.try_reserve("a", now=t0, is_revision=False)
    second = await store.try_reserve("a", now=t0, is_revision=False)
    assert first.outcome is DedupReserveOutcome.RESERVED
    assert second.outcome is DedupReserveOutcome.DUPLICATE
    assert second.existing_state is DedupEntryState.RESERVED


@pytest.mark.asyncio
async def test_revision_skips_reservation() -> None:
    store = BoundedDedupStore(ttl=timedelta(seconds=60), max_entries=10)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    await store.try_reserve("a", now=t0, is_revision=False)
    await store.commit("a", now=t0)
    revision = await store.try_reserve("a", now=t0, is_revision=True)
    assert revision.outcome is DedupReserveOutcome.SKIPPED_REVISION


@pytest.mark.asyncio
async def test_ttl_expiry_allows_reprocessing() -> None:
    store = BoundedDedupStore(ttl=timedelta(seconds=10), max_entries=10)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    await store.try_reserve("a", now=t0, is_revision=False)
    await store.commit("a", now=t0)
    expired = await store.try_reserve("a", now=t0 + timedelta(seconds=11), is_revision=False)
    assert expired.outcome is DedupReserveOutcome.RESERVED


@pytest.mark.asyncio
async def test_deterministic_max_size_evicts_oldest_committed() -> None:
    store = BoundedDedupStore(ttl=timedelta(hours=1), max_entries=2)
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    await store.try_reserve("a", now=t0, is_revision=False)
    await store.commit("a", now=t0)
    await store.try_reserve("b", now=t0 + timedelta(seconds=1), is_revision=False)
    await store.commit("b", now=t0 + timedelta(seconds=1))
    third = await store.try_reserve("c", now=t0 + timedelta(seconds=2), is_revision=False)
    assert third.outcome is DedupReserveOutcome.RESERVED
    assert len(store) == 2
    # Oldest committed "a" evicted; "b" remains committed and still suppresses.
    replay_b = await store.try_reserve("b", now=t0 + timedelta(seconds=3), is_revision=False)
    assert replay_b.outcome is DedupReserveOutcome.DUPLICATE
    # Store is b(committed)+c(reserved). Evicted "a" may be reserved again after releasing c.
    await store.release("c")
    replay_a = await store.try_reserve("a", now=t0 + timedelta(seconds=3), is_revision=False)
    assert replay_a.outcome is DedupReserveOutcome.RESERVED
