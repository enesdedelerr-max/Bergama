"""Replay-compatible Strategy Engine integration tests (#401)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from app.core.clock import FixedClock
from app.market_data.replay.models import ReplayMode, ReplayRequest
from tests.support.market_data_fixtures import T0, make_bar
from tests.support.replay_helpers import build_offline_replay_stack
from tests.support.strategy_helpers import (
    noop_config,
    quality_assessment,
    strategy_engine,
    strategy_identity,
)


def _request() -> ReplayRequest:
    return ReplayRequest(
        start_time=T0 - timedelta(minutes=1),
        end_time=T0 + timedelta(minutes=1),
        max_records=10,
        mode=ReplayMode.DRY_RUN,
    )


@pytest.mark.asyncio
async def test_strategy_engine_consumes_replay_source_canonical_events(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    event = make_bar()
    replay_engine, source, _store, _writer = build_offline_replay_stack(
        tmp_path,
        clock=clock,
        events=[event],
    )
    records = await source.fetch(_request())
    engine, port = strategy_engine(clock=clock)
    session = engine.create_session(
        run_id="replay-run-1",
        session_id="replay-session-1",
        strategies=((strategy_identity(), noop_config()),),
    )

    decisions = []
    for record in records:
        decisions.extend(
            await session.evaluate(
                record.event,
                quality_assessment=quality_assessment(record.event),
                correlation_id="corr-replay-1",
                causation_id=record.idempotency_key,
            )
        )

    assert len(decisions) == 1
    assert port.decisions[0].decision_id == decisions[0].decision_id
    assert decisions[0].causation_id == records[0].idempotency_key
    assert decisions[0].instrument_id.instrument_key == event.instrument.instrument_key
    await replay_engine.aclose()


@pytest.mark.asyncio
async def test_replay_strategy_decision_is_stable_for_same_run_context(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    event = make_bar()
    replay_engine, source, _store, _writer = build_offline_replay_stack(
        tmp_path,
        clock=clock,
        events=[event],
    )
    record = (await source.fetch(_request()))[0]
    identity = strategy_identity()
    config = noop_config()

    engine_a, _ = strategy_engine(clock=clock)
    engine_b, _ = strategy_engine(clock=clock)
    decision_a = (
        await engine_a.create_session(
            run_id="replay-run-1",
            session_id="replay-session-1",
            strategies=((identity, config),),
        ).evaluate(record.event, quality_assessment=quality_assessment(record.event))
    )[0]
    decision_b = (
        await engine_b.create_session(
            run_id="replay-run-1",
            session_id="replay-session-1",
            strategies=((identity, config),),
        ).evaluate(record.event, quality_assessment=quality_assessment(record.event))
    )[0]

    assert decision_a == decision_b
    await replay_engine.aclose()
