"""Optional local Replay Engine smoke (#308).

Opt-in: BERGAMA_REPLAY_ENGINE_SMOKE=1

Uses local SqlCatalog/file Iceberg tables only. Default mode dry_run.
No provider credentials. No production Kafka sink.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pytest
from app.core.clock import FixedClock
from app.market_data.replay.models import ReplayMode, ReplayRequest
from app.market_data.replay.policies import NoOpReplaySleeper
from tests.support.market_data_fixtures import T0, make_quote, make_trade
from tests.support.replay_helpers import build_offline_replay_stack

pytestmark = pytest.mark.replay_engine_smoke


@pytest.mark.asyncio
async def test_replay_engine_local_smoke(tmp_path: Path) -> None:
    if os.environ.get("BERGAMA_REPLAY_ENGINE_SMOKE") != "1":
        pytest.skip("BERGAMA_REPLAY_ENGINE_SMOKE not set")

    clock = FixedClock(T0)
    events = [
        make_quote(),
        make_trade(source=make_trade().source.model_copy(update={"source_event_id": "smoke-t"})),
    ]
    engine, _source, store, _writer = build_offline_replay_stack(
        tmp_path, clock=clock, events=events
    )
    engine.sleeper = NoOpReplaySleeper()
    request = ReplayRequest(
        start_time=T0 - timedelta(hours=1),
        end_time=T0 + timedelta(hours=1),
        max_records=10,
        mode=ReplayMode.DRY_RUN,
    )
    result = await engine.run(request, replay_id="smoke-replay-1")
    assert result.succeeded_count == 2
    assert result.terminal_status == "completed"
    ck = await store.load("smoke-replay-1")
    assert ck is not None
    assert ck.completed is True
    assert ck.last_cursor is not None
    await engine.aclose()
