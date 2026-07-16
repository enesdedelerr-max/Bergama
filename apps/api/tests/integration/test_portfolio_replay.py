"""Portfolio replay and determinism integration tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from random import Random

import pytest
from app.portfolio.hashing import snapshot_hash_payload
from app.portfolio.models import FillAppliedCommand, FillSide, PortfolioMutationOutcome
from app.strategy.keys import canonical_strategy_json
from tests.support.portfolio_helpers import (
    account_id,
    fill_command,
    portfolio_id,
    portfolio_service,
)

FIXED_REPLAY_SEEDS = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55]


def _stable_1000_fill_stream(seed: int) -> tuple[FillAppliedCommand, ...]:
    rng = Random(seed)
    events: list[FillAppliedCommand] = []
    for idx in range(1, 1001):
        side = FillSide.BUY if idx <= 500 else FillSide.SELL
        price = f"{100 + rng.randint(-5, 5)}.{rng.randint(0, 99):02d}"
        events.append(
            fill_command(
                idx=idx,
                side=side,
                quantity="1",
                price=price,
                expected_version=idx - 1,
            )
        )
    return tuple(events)


async def _run_stream(events: tuple[FillAppliedCommand, ...], *, service=None):
    svc = service or portfolio_service()
    try:
        await svc.get_snapshot(portfolio_id())
    except Exception:
        await svc.create_portfolio(
            account_id=account_id(),
            portfolio_id=portfolio_id(),
            snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
        )
    results = []
    for event in events:
        results.append(await svc.apply_fill(event))
    return svc, tuple(results)


@pytest.mark.asyncio
async def test_1000_event_replay_is_deterministic() -> None:
    assert FIXED_REPLAY_SEEDS == [0, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    for seed in FIXED_REPLAY_SEEDS:
        events = _stable_1000_fill_stream(seed)
        service_a, results_a = await _run_stream(events)
        service_b, results_b = await _run_stream(events)
        snapshot_a = await service_a.get_snapshot(portfolio_id())
        snapshot_b = await service_b.get_snapshot(portfolio_id())
        ledger_a = await service_a.get_ledger(portfolio_id())
        ledger_b = await service_b.get_ledger(portfolio_id())
        snapshot_a_json = canonical_strategy_json(snapshot_hash_payload(snapshot_a))
        snapshot_b_json = canonical_strategy_json(snapshot_hash_payload(snapshot_b))
        assert snapshot_a_json == snapshot_b_json
        assert snapshot_a.snapshot_hash == snapshot_b.snapshot_hash
        assert tuple(entry.ledger_entry_id for entry in ledger_a) == tuple(
            entry.ledger_entry_id for entry in ledger_b
        )
        assert snapshot_a.portfolio_version == snapshot_b.portfolio_version == 1000
        assert all(result.outcome is PortfolioMutationOutcome.APPLIED for result in results_a)
        assert results_a == results_b


@pytest.mark.asyncio
async def test_replaying_same_1000_events_again_only_returns_duplicates() -> None:
    events = _stable_1000_fill_stream(FIXED_REPLAY_SEEDS[0])
    service, _ = await _run_stream(events)
    snapshot_before = await service.get_snapshot(portfolio_id())
    ledger_before = await service.get_ledger(portfolio_id())
    _, duplicate_results = await _run_stream(events, service=service)
    assert all(result.outcome is PortfolioMutationOutcome.DUPLICATE for result in duplicate_results)
    assert await service.get_snapshot(portfolio_id()) == snapshot_before
    assert await service.get_ledger(portfolio_id()) == ledger_before


@pytest.mark.asyncio
async def test_midpoint_snapshot_restore_reaches_same_final_hash() -> None:
    events = _stable_1000_fill_stream(FIXED_REPLAY_SEEDS[1])
    service_full, _ = await _run_stream(events)
    full_snapshot = await service_full.get_snapshot(portfolio_id())

    service_mid, _ = await _run_stream(events[:500])
    midpoint_snapshot = await service_mid.get_snapshot(portfolio_id())
    restored = portfolio_service()
    await restored._repository.create_portfolio(midpoint_snapshot)  # noqa: SLF001
    _, _ = await _run_stream(events[500:], service=restored)
    restored_snapshot = await restored.get_snapshot(portfolio_id())
    assert restored_snapshot.snapshot_hash == full_snapshot.snapshot_hash


@pytest.mark.asyncio
async def test_two_portfolios_process_equivalent_streams_without_leakage() -> None:
    first = portfolio_service()
    second = portfolio_service()
    events = _stable_1000_fill_stream(FIXED_REPLAY_SEEDS[2])
    await _run_stream(events, service=first)
    await _run_stream(events, service=second)
    assert (await first.get_snapshot(portfolio_id())).snapshot_hash == (
        await second.get_snapshot(portfolio_id())
    ).snapshot_hash
    assert await first.get_ledger(portfolio_id()) == await second.get_ledger(portfolio_id())


@pytest.mark.asyncio
async def test_concurrent_duplicate_fill_in_replay_commits_once() -> None:
    service = portfolio_service()
    await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    event = fill_command(idx=1, side=FillSide.BUY, quantity="1", price="100")
    results = await asyncio.gather(service.apply_fill(event), service.apply_fill(event))
    assert sorted(result.outcome.value for result in results) == ["APPLIED", "DUPLICATE"]
    assert len(await service.get_ledger(portfolio_id())) == 1
