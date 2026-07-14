"""Unit tests for per-stream sequencing (#305)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from app.market_data.orchestrator.sequencing import PerStreamSequencer, StreamLease
from tests.support.orchestrator_events import EVENT_TIME, equity, quote_event, trade_event


@pytest.mark.asyncio
async def test_same_stream_preserves_serialized_acquisition_order() -> None:
    seq = PerStreamSequencer()
    order: list[int] = []
    first_holding = asyncio.Event()
    release_first = asyncio.Event()

    async def hold_first() -> None:
        lease = await seq.acquire(trade_event(source_event_id="t1"))
        order.append(lease.info.sequence)
        first_holding.set()
        await release_first.wait()
        await lease.release()

    second_started = asyncio.Event()

    async def take_second() -> StreamLease:
        await first_holding.wait()
        second_started.set()
        return await seq.acquire(trade_event(source_event_id="t2"))

    t1 = asyncio.create_task(hold_first())
    await first_holding.wait()
    t2 = asyncio.create_task(take_second())
    await second_started.wait()
    done, _pending = await asyncio.wait({t2}, timeout=0.05)
    assert t2 not in done
    release_first.set()
    await t1
    second = await t2
    order.append(second.info.sequence)
    await second.release()
    assert order == [1, 2]


@pytest.mark.asyncio
async def test_different_instruments_do_not_block() -> None:
    seq = PerStreamSequencer()
    aapl = await seq.acquire(trade_event(source_event_id="a1"))
    msft = await seq.acquire(
        trade_event(
            source_event_id="m1",
            instrument=equity(key="bergama:equity:us:msft", symbol="MSFT"),
        )
    )
    assert aapl.info.stream_key != msft.info.stream_key
    await msft.release()
    await aapl.release()


@pytest.mark.asyncio
async def test_different_event_types_are_separate_streams() -> None:
    seq = PerStreamSequencer()
    trade = await seq.acquire(trade_event(source_event_id="t1"))
    quote = await seq.acquire(quote_event(source_event_id="q1"))
    assert trade.info.stream_key != quote.info.stream_key
    await quote.release()
    await trade.release()


@pytest.mark.asyncio
async def test_out_of_order_timestamps_flagged_not_reordered() -> None:
    seq = PerStreamSequencer()
    first = await seq.acquire(trade_event(source_event_id="a", occurred_at=EVENT_TIME))
    await first.release()
    second = await seq.acquire(
        trade_event(source_event_id="b", occurred_at=EVENT_TIME - timedelta(minutes=1))
    )
    assert first.info.sequence == 1
    assert second.info.sequence == 2
    assert second.info.out_of_order is True
    await second.release()


@pytest.mark.asyncio
async def test_release_idempotent_after_failure_path() -> None:
    seq = PerStreamSequencer()
    lease = await seq.acquire(trade_event(source_event_id="x"))
    await lease.release()
    await lease.release()
    again = await seq.acquire(trade_event(source_event_id="y"))
    await again.release()


@pytest.mark.asyncio
async def test_stream_state_bounded() -> None:
    seq = PerStreamSequencer(max_idle_streams=2)
    for i in range(5):
        lease = await seq.acquire(
            trade_event(
                source_event_id=f"s{i}",
                instrument=equity(key=f"bergama:equity:us:s{i}", symbol=f"S{i}"),
            )
        )
        await lease.release()
    assert len(seq) <= 2
