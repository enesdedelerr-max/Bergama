"""Offline Iceberg Replay Engine integration (#308)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.replay_settings import ReplaySettings
from app.infrastructure.iceberg.catalog import build_offline_sql_settings
from app.market_data.replay.errors import ReplayClosedError, ReplaySinkFailedError
from app.market_data.replay.models import ReplayMode, ReplayRequest
from app.market_data.replay.policies import NoOpReplaySleeper
from tests.support.market_data_fixtures import (
    T0,
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
)
from tests.support.recording_publish_port import RecordingPublishPort
from tests.support.replay_helpers import build_offline_replay_stack


def _range_request(**overrides: object) -> ReplayRequest:
    data: dict[str, object] = {
        "start_time": T0 - timedelta(hours=1),
        "end_time": T0 + timedelta(hours=2),
        "max_records": 100,
        "mode": ReplayMode.DRY_RUN,
    }
    data.update(overrides)
    return ReplayRequest.model_validate(data)


@pytest.mark.asyncio
async def test_dry_run_from_seeded_tables(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    events = [
        make_quote(),
        make_trade(source=make_trade().source.model_copy(update={"source_event_id": "t1"})),
        make_bar(),
        make_reference(),
        make_fundamental(),
        make_macro(),
        make_filing(),
        make_news(),
    ]
    engine, _source, store, _writer = build_offline_replay_stack(
        tmp_path, clock=clock, events=events
    )
    engine.sleeper = NoOpReplaySleeper()
    result = await engine.run(_range_request(), replay_id="offline-dry")
    assert result.succeeded_count == 8
    assert result.terminal_status == "completed"
    assert result.sink_type == "none"
    ck = await store.load("offline-dry")
    assert ck is not None and ck.completed is True
    assert result.synthetic_reconstruction_count == 8
    await engine.aclose()


@pytest.mark.asyncio
async def test_validate_only_and_republish(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    events = [
        make_quote(),
        make_trade(source=make_trade().source.model_copy(update={"source_event_id": "t2"})),
    ]
    engine, _s, _store, _w = build_offline_replay_stack(tmp_path, clock=clock, events=events)
    engine.sleeper = NoOpReplaySleeper()
    validated = await engine.run(
        _range_request(mode=ReplayMode.VALIDATE_ONLY),
        replay_id="offline-val",
    )
    assert validated.succeeded_count == 2

    port = RecordingPublishPort(clock=clock)
    published = await engine.run(
        _range_request(mode=ReplayMode.REPUBLISH),
        replay_id="offline-rep",
        publish_port=port,
    )
    assert published.succeeded_count == 2
    assert len(port.published) == 2
    await engine.aclose()


@pytest.mark.asyncio
async def test_resume_after_controlled_sink_failure(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    events = [
        make_quote(source=make_quote().source.model_copy(update={"source_event_id": "q-a"})),
        make_quote(source=make_quote().source.model_copy(update={"source_event_id": "q-b"})),
    ]
    engine, _s, store, _w = build_offline_replay_stack(tmp_path, clock=clock, events=events)
    engine.sleeper = NoOpReplaySleeper()
    port = RecordingPublishPort(clock=clock)
    port.set_fail_next(True)
    # Force first event to succeed then fail: flip after first call.
    # RecordingPublishPort fail_next fails the next call only; seed succeed first via two-phase.
    # First call succeeds (fail_next false initially), set fail before second via custom port.

    class FailSecond:
        def __init__(self) -> None:
            self.n = 0
            self.inner = RecordingPublishPort(clock=clock)

        async def publish(self, event, *, routing_key, context):  # type: ignore[no-untyped-def]
            self.n += 1
            if self.n == 2:
                self.inner.set_fail_next(True)
            return await self.inner.publish(event, routing_key=routing_key, context=context)

    flaky = FailSecond()
    with pytest.raises(ReplaySinkFailedError):
        await engine.run(
            _range_request(mode=ReplayMode.REPUBLISH),
            replay_id="offline-resume",
            publish_port=flaky,  # type: ignore[arg-type]
        )
    ck = await store.load("offline-resume")
    assert ck is not None
    assert ck.succeeded_count == 1
    assert ck.completed is False

    port2 = RecordingPublishPort(clock=clock)
    result = await engine.run(
        _range_request(mode=ReplayMode.REPUBLISH, resume=True, checkpoint_id="offline-resume"),
        replay_id="offline-resume",
        publish_port=port2,
    )
    assert result.succeeded_count == 2
    assert len(port2.published) == 1
    await engine.aclose()


@pytest.mark.asyncio
async def test_container_no_startup_replay_and_isolation(tmp_path: Path) -> None:
    warehouse = tmp_path / "wh"
    writer = build_offline_sql_settings(warehouse)
    ck = tmp_path / "ck"
    ck.mkdir()
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        iceberg_writer=writer.model_copy(update={"enabled": False}),
        replay=ReplaySettings(
            enabled=True,
            checkpoint_directory=str(ck.resolve()),
        ),
    )
    container = build_container(settings)
    assert container.replay_engine is not None
    assert container.market_data_orchestrator is None
    await container.aclose()
    with pytest.raises(ReplayClosedError):
        await container.replay_engine.run(_range_request(), replay_id="nope")
