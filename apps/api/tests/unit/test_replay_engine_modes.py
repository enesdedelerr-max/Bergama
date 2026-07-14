"""Replay modes, identity, isolation, and checkpoint unit tests (#308)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from app.core.clock import FixedClock
from app.core.replay_settings import ReplaySettings
from app.infrastructure.replay.file_checkpoint import FileCheckpointStore
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.ports import PublishResult
from app.market_data.replay.audit import InMemoryReplayAuditSink
from app.market_data.replay.checkpoint import ReplayCheckpoint
from app.market_data.replay.engine import build_replay_engine
from app.market_data.replay.errors import (
    ReplayCheckpointCorruptError,
    ReplayCheckpointMismatchError,
    ReplayClosedError,
    ReplayCompletedError,
    ReplaySinkFailedError,
    ReplaySinkRequiredError,
)
from app.market_data.replay.models import ReplayMode, ReplayRecord, ReplayRequest
from app.market_data.replay.policies import NoOpReplaySleeper
from tests.support.market_data_fixtures import T0, make_quote, make_trade
from tests.support.recording_publish_port import RecordingPublishPort


class FakeReplaySource:
    def __init__(self, records: list[ReplayRecord]) -> None:
        self.records = records
        self.closed = False

    async def fetch(self, request: ReplayRequest) -> list[ReplayRecord]:
        _ = request
        return list(self.records)

    async def aclose(self) -> None:
        self.closed = True


def _record_for(event: object, *, table_base: str, event_type: str) -> ReplayRecord:
    return ReplayRecord(
        occurred_at=event.occurred_at,  # type: ignore[attr-defined]
        event_type=event_type,
        instrument_key=event.instrument.instrument_key,  # type: ignore[attr-defined]
        idempotency_key=build_idempotency_key(event),  # type: ignore[arg-type]
        table_base=table_base,
        event=event,  # type: ignore[arg-type]
        synthetic_symbol_effective_from=True,
    )


def _settings(tmp_path: Any) -> ReplaySettings:
    directory = tmp_path / "ck"
    directory.mkdir(exist_ok=True)
    return ReplaySettings(
        enabled=True,
        checkpoint_directory=str(directory.resolve()),
        max_records=1000,
    )


def _request(**overrides: Any) -> ReplayRequest:
    data: dict[str, Any] = {
        "start_time": T0 - timedelta(hours=1),
        "end_time": T0 + timedelta(hours=1),
        "max_records": 100,
        "mode": ReplayMode.DRY_RUN,
    }
    data.update(overrides)
    return ReplayRequest.model_validate(data)


@pytest.mark.asyncio
async def test_dry_run_and_validate_only_never_call_sink(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    quote = make_quote()
    records = [_record_for(quote, table_base="market_quotes", event_type="market.quote")]
    port = RecordingPublishPort(clock=clock)
    audit = InMemoryReplayAuditSink()
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource(records),
        checkpoint_store=FileCheckpointStore((tmp_path / "ck").resolve()),
        audit_sink=audit,
        sleeper=NoOpReplaySleeper(),
    )
    result = await engine.run(_request(mode=ReplayMode.DRY_RUN), replay_id="dry-1")
    assert result.terminal_status in {"completed", "completed_empty"}
    assert result.succeeded_count == 1
    assert port.published == []
    assert all(e.decision.value != "REPUBLISHED" for e in audit.events)
    assert all(e.decision.value == "DRY_RUN_VALIDATED" for e in audit.events)

    result2 = await engine.run(
        _request(mode=ReplayMode.VALIDATE_ONLY),
        replay_id="val-1",
    )
    assert result2.succeeded_count == 1
    assert port.published == []
    assert audit.events[-1].decision.value == "VALIDATED"
    await engine.aclose()


@pytest.mark.asyncio
async def test_republish_requires_explicit_sink(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    quote = make_quote()
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource(
            [_record_for(quote, table_base="market_quotes", event_type="market.quote")]
        ),
        checkpoint_store=FileCheckpointStore((tmp_path / "ck").resolve()),
        sleeper=NoOpReplaySleeper(),
    )
    with pytest.raises(ReplaySinkRequiredError):
        await engine.run(_request(mode=ReplayMode.REPUBLISH), replay_id="r1")
    with pytest.raises(ReplaySinkRequiredError):
        await engine.run(_request(mode=ReplayMode.CUSTOM_SINK), replay_id="r2")
    await engine.aclose()


@pytest.mark.asyncio
async def test_republish_preserves_idempotency_key(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    quote = make_quote()
    key = build_idempotency_key(quote)
    port = RecordingPublishPort(clock=clock)
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource(
            [_record_for(quote, table_base="market_quotes", event_type="market.quote")]
        ),
        checkpoint_store=FileCheckpointStore((tmp_path / "ck").resolve()),
        sleeper=NoOpReplaySleeper(),
    )
    result = await engine.run(
        _request(mode=ReplayMode.REPUBLISH),
        replay_id="rep-1",
        publish_port=port,
    )
    assert result.succeeded_count == 1
    assert len(port.published) == 1
    assert port.published[0][2].idempotency_key == key
    await engine.aclose()


@pytest.mark.asyncio
async def test_fresh_orchestrator_dedup_per_run(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    quote = make_quote()
    port = RecordingPublishPort(clock=clock)
    source = FakeReplaySource(
        [_record_for(quote, table_base="market_quotes", event_type="market.quote")]
    )
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=source,
        checkpoint_store=FileCheckpointStore((tmp_path / "ck").resolve()),
        sleeper=NoOpReplaySleeper(),
    )
    await engine.run(
        _request(mode=ReplayMode.REPUBLISH, allow_completed_rerun=True),
        replay_id="iso-1",
        publish_port=port,
    )
    await engine.run(
        _request(mode=ReplayMode.REPUBLISH, allow_completed_rerun=True),
        replay_id="iso-1",
        publish_port=port,
    )
    # At-least-once: second run publishes again with fresh dedup store.
    assert len(port.published) == 2
    await engine.aclose()


@pytest.mark.asyncio
async def test_checkpoint_resume_and_failed_non_advance(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    q1 = make_quote(source=make_quote().source.model_copy(update={"source_event_id": "a"}))
    q2 = make_trade(source=make_trade().source.model_copy(update={"source_event_id": "b"}))
    records = [
        _record_for(q1, table_base="market_quotes", event_type="market.quote"),
        _record_for(q2, table_base="market_trades", event_type="market.trade"),
    ]
    store = FileCheckpointStore((tmp_path / "ck").resolve())

    class FlakyPort:
        def __init__(self) -> None:
            self.calls = 0
            self.published: list[Any] = []

        async def publish(
            self,
            event: Any,
            *,
            routing_key: str,
            context: PipelineContext,
        ) -> PublishResult:
            self.calls += 1
            if self.calls == 2:
                return PublishResult(succeeded=False, published_at=clock.now())
            self.published.append(event)
            return PublishResult(
                succeeded=True,
                published_at=clock.now(),
                sink_message_id=f"m-{self.calls}",
                idempotency_acknowledged=True,
            )

    port = FlakyPort()
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource(records),
        checkpoint_store=store,
        sleeper=NoOpReplaySleeper(),
    )
    with pytest.raises(ReplaySinkFailedError):
        await engine.run(
            _request(mode=ReplayMode.REPUBLISH),
            replay_id="resume-1",
            publish_port=port,  # type: ignore[arg-type]
        )
    ck = await store.load("resume-1")
    assert ck is not None
    assert ck.succeeded_count == 1
    assert ck.last_cursor is not None
    assert ck.last_cursor.idempotency_key == build_idempotency_key(q1)
    assert ck.completed is False

    port2 = RecordingPublishPort(clock=clock)
    result = await engine.run(
        _request(mode=ReplayMode.REPUBLISH, resume=True, checkpoint_id="resume-1"),
        replay_id="resume-1",
        publish_port=port2,
    )
    assert result.succeeded_count == 2
    assert len(port2.published) == 1
    assert build_idempotency_key(port2.published[0][0]) == build_idempotency_key(q2)
    await engine.aclose()


@pytest.mark.asyncio
async def test_corrupt_and_mismatch_checkpoint(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    store = FileCheckpointStore((tmp_path / "ck").resolve())
    path = (tmp_path / "ck" / "bad.json").resolve()
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ReplayCheckpointCorruptError):
        await store.load("bad")

    quote = make_quote()
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource(
            [_record_for(quote, table_base="market_quotes", event_type="market.quote")]
        ),
        checkpoint_store=store,
        sleeper=NoOpReplaySleeper(),
    )
    await engine.run(_request(mode=ReplayMode.DRY_RUN), replay_id="fp-1")
    with pytest.raises(ReplayCheckpointMismatchError):
        await engine.run(
            _request(mode=ReplayMode.VALIDATE_ONLY, resume=True, checkpoint_id="fp-1"),
            replay_id="fp-1",
        )
    with pytest.raises(ReplayCompletedError):
        await engine.run(
            _request(mode=ReplayMode.DRY_RUN, resume=True, checkpoint_id="fp-1"),
            replay_id="fp-1",
        )
    await engine.aclose()


@pytest.mark.asyncio
async def test_close_idempotent_and_run_after_close(tmp_path: Any) -> None:
    clock = FixedClock(T0)
    engine = build_replay_engine(
        _settings(tmp_path),
        clock=clock,
        source=FakeReplaySource([]),
        checkpoint_store=FileCheckpointStore((tmp_path / "ck").resolve()),
        sleeper=NoOpReplaySleeper(),
    )
    await engine.aclose()
    await engine.aclose()
    with pytest.raises(ReplayClosedError):
        await engine.run(_request(), replay_id="x")


@pytest.mark.asyncio
async def test_atomic_checkpoint_json(tmp_path: Any) -> None:
    store = FileCheckpointStore((tmp_path / "ck").resolve())
    ck = ReplayCheckpoint(
        replay_id="atomic-1",
        request_fingerprint="a" * 64,
        mode=ReplayMode.DRY_RUN,
        started_at=T0,
        updated_at=T0,
        processed_count=1,
        succeeded_count=1,
    )
    await store.save(ck)
    loaded = await store.load("atomic-1")
    assert loaded is not None
    assert loaded.processed_count == 1
    await store.aclose()
