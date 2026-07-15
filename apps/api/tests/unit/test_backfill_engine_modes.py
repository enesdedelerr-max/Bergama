"""Unit tests for Backfill engine modes, failures, ordering, lifecycle (#309)."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.market_data.backfill.errors import (
    BackfillAuthError,
    BackfillCancelledError,
    BackfillCheckpointMismatchError,
    BackfillClosedError,
    BackfillCompletedError,
    BackfillSinkFailedError,
    BackfillSinkRequiredError,
    BackfillTruncatedError,
)
from app.market_data.backfill.models import BackfillMode
from app.market_data.keys import build_idempotency_key
from tests.support.backfill_helpers import (
    FakeBackfillSource,
    build_engine,
    polygon_request,
    two_day_bar_source,
)
from tests.support.market_data_fixtures import make_bar
from tests.support.recording_publish_port import RecordingPublishPort


@pytest.mark.asyncio
async def test_dry_run_no_sink_never_reports_published(tmp_path: Path) -> None:
    engine, store, _ = build_engine(tmp_path, two_day_bar_source())
    result = await engine.run(polygon_request(), backfill_id="dry-1")
    assert result.terminal_status == "completed"
    assert result.processed_count == 2
    assert result.published_count == 0
    assert result.sink_type == "none"
    ck = await store.load("dry-1")
    assert ck is not None and ck.completed is True
    assert all(e.decision.value.startswith("DRY_RUN") for e in engine.audit_sink.events)  # type: ignore[attr-defined]
    await engine.aclose()


@pytest.mark.asyncio
async def test_validate_only_no_sink(tmp_path: Path) -> None:
    engine, _, _ = build_engine(tmp_path, two_day_bar_source())
    result = await engine.run(
        polygon_request(mode=BackfillMode.VALIDATE_ONLY),
        backfill_id="val-1",
    )
    assert result.published_count == 0
    assert result.processed_count == 2
    await engine.aclose()


@pytest.mark.asyncio
async def test_publish_requires_explicit_sink(tmp_path: Path) -> None:
    engine, _, clock = build_engine(tmp_path, two_day_bar_source())
    with pytest.raises(BackfillSinkRequiredError):
        await engine.run(
            polygon_request(mode=BackfillMode.PUBLISH),
            backfill_id="pub-missing",
        )
    port = RecordingPublishPort(clock=clock)
    result = await engine.run(
        polygon_request(mode=BackfillMode.PUBLISH),
        backfill_id="pub-ok",
        publish_port=port,
    )
    assert result.published_count == 2
    assert len(port.published) == 2
    await engine.aclose()


@pytest.mark.asyncio
async def test_may_have_more_fails_closed(tmp_path: Path) -> None:
    source = two_day_bar_source()
    source.may_have_more_slices.add("day-0000-2024-01-02")
    engine, store, _ = build_engine(tmp_path, source)
    with pytest.raises(BackfillTruncatedError):
        await engine.run(polygon_request(), backfill_id="trunc")
    ck = await store.load("trunc")
    assert ck is not None
    assert ck.completed is False
    await engine.aclose()


@pytest.mark.asyncio
async def test_auth_failure_terminal(tmp_path: Path) -> None:
    source = FakeBackfillSource(raise_on_fetch=BackfillAuthError(detail="denied"))
    engine, _, _ = build_engine(tmp_path, source)
    with pytest.raises(BackfillAuthError):
        await engine.run(polygon_request(), backfill_id="auth")
    await engine.aclose()


@pytest.mark.asyncio
async def test_stable_ordering_and_idempotency_keys(tmp_path: Path) -> None:
    from datetime import UTC, datetime, timedelta

    late = datetime(2024, 1, 2, 15, 30, tzinfo=UTC)
    early = datetime(2024, 1, 2, 14, 0, tzinfo=UTC)
    bar_a = make_bar(
        occurred_at=late,
        effective_at=late,
        close_time=late,
        window_start=late - timedelta(minutes=1),
        window_end=late,
        source=make_bar().source.model_copy(update={"source_event_id": "z-late"}),
    )
    bar_b = make_bar(
        occurred_at=early,
        effective_at=early,
        close_time=early,
        window_start=early - timedelta(minutes=1),
        window_end=early,
        source=make_bar().source.model_copy(update={"source_event_id": "a-early"}),
    )
    # Same slice; reverse insertion order — engine must reorder.
    source = FakeBackfillSource(
        events_by_slice={"day-0000-2024-01-02": [bar_a, bar_b]},
        slices=two_day_bar_source().build_slices(polygon_request())[:1],
    )
    engine, _, _ = build_engine(tmp_path, source)
    await engine.run(
        polygon_request(end_time=polygon_request().start_time.replace(day=3)),
        backfill_id="order",
    )
    keys = [e.idempotency_key for e in engine.audit_sink.events]  # type: ignore[attr-defined]
    # Deterministic: earlier occurred_at first (slice_start equal).
    assert keys == [build_idempotency_key(bar_b), build_idempotency_key(bar_a)]
    await engine.aclose()


@pytest.mark.asyncio
async def test_resume_after_sink_failure(tmp_path: Path) -> None:
    source = two_day_bar_source()
    engine, store, clock = build_engine(tmp_path, source)

    class FailSecond:
        def __init__(self) -> None:
            self.n = 0
            self.inner = RecordingPublishPort(clock=clock)

        async def publish(self, event, *, routing_key, context):  # type: ignore[no-untyped-def]
            self.n += 1
            if self.n == 2:
                self.inner.set_fail_next(True)
            return await self.inner.publish(event, routing_key=routing_key, context=context)

    with pytest.raises(BackfillSinkFailedError):
        await engine.run(
            polygon_request(mode=BackfillMode.PUBLISH),
            backfill_id="resume-sink",
            publish_port=FailSecond(),  # type: ignore[arg-type]
        )
    ck = await store.load("resume-sink")
    assert ck is not None
    assert ck.published_count == 1
    assert ck.completed is False

    port2 = RecordingPublishPort(clock=clock)
    result = await engine.run(
        polygon_request(
            mode=BackfillMode.PUBLISH,
            resume=True,
            checkpoint_id="resume-sink",
        ),
        backfill_id="resume-sink",
        publish_port=port2,
    )
    assert result.published_count == 2
    assert len(port2.published) == 1
    await engine.aclose()


@pytest.mark.asyncio
async def test_completed_rerun_requires_flag(tmp_path: Path) -> None:
    engine, _, _ = build_engine(tmp_path, two_day_bar_source())
    await engine.run(polygon_request(), backfill_id="done")
    with pytest.raises(BackfillCompletedError):
        await engine.run(polygon_request(resume=True), backfill_id="done")
    result = await engine.run(
        polygon_request(allow_completed_rerun=True),
        backfill_id="done",
    )
    assert result.processed_count == 2
    await engine.aclose()


@pytest.mark.asyncio
async def test_fingerprint_mismatch(tmp_path: Path) -> None:
    source = two_day_bar_source()
    engine, store, _ = build_engine(tmp_path, source)

    async def cancel_after_fetch(slice_, request):  # type: ignore[no-untyped-def]
        result = await FakeBackfillSource.fetch_slice(source, slice_, request)
        engine.request_cancel()
        return result

    source.fetch_slice = cancel_after_fetch  # type: ignore[method-assign]
    with pytest.raises(BackfillCancelledError):
        await engine.run(polygon_request(max_records=50), backfill_id="fp2")
    with pytest.raises(BackfillCheckpointMismatchError):
        await engine.run(
            polygon_request(max_records=99, resume=True),
            backfill_id="fp2",
        )
    ck = await store.load("fp2")
    assert ck is not None and ck.completed is False
    await engine.aclose()


@pytest.mark.asyncio
async def test_close_idempotent_and_run_after_close(tmp_path: Path) -> None:
    engine, _, _ = build_engine(tmp_path, two_day_bar_source())
    await engine.aclose()
    await engine.aclose()
    with pytest.raises(BackfillClosedError):
        await engine.run(polygon_request(), backfill_id="closed")


@pytest.mark.asyncio
async def test_cancellation_persists_incomplete(tmp_path: Path) -> None:
    source = two_day_bar_source()
    engine, store, _ = build_engine(tmp_path, source)

    async def cancel_after_fetch(slice_, request):  # type: ignore[no-untyped-def]
        result = await FakeBackfillSource.fetch_slice(source, slice_, request)
        engine.request_cancel()
        return result

    source.fetch_slice = cancel_after_fetch  # type: ignore[method-assign]
    with pytest.raises(BackfillCancelledError):
        await engine.run(polygon_request(), backfill_id="cancel")
    ck = await store.load("cancel")
    assert ck is not None
    assert ck.completed is False
    await engine.aclose()
