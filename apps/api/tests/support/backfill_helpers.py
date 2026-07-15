"""Test helpers for Historical Backfill Pipeline (#309)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.backfill_settings import BackfillSettings
from app.core.clock import FixedClock
from app.infrastructure.backfill.file_checkpoint import FileBackfillCheckpointStore
from app.market_data.backfill.engine import (
    BackfillEngine,
    StaticSourceRegistry,
    build_backfill_engine,
)
from app.market_data.backfill.models import (
    BackfillMode,
    BackfillProvider,
    BackfillRequest,
    BackfillSlice,
    BackfillSourceKind,
    PolygonSelector,
)
from app.market_data.backfill.policies import NoOpBackfillSleeper
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_idempotency_key
from tests.support.market_data_fixtures import T0, instrument, make_bar


def backfill_settings(tmp_path: Path, **overrides: object) -> BackfillSettings:
    data: dict[str, object] = {
        "enabled": True,
        "default_mode": "dry_run",
        "checkpoint_enabled": True,
        "checkpoint_directory": str(tmp_path / "backfill-ck"),
        "max_time_range_days": 31,
        "max_records": 10_000,
        "max_slices": 366,
        "max_concurrent_slices": 1,
        "max_in_flight_events": 1,
        "slice_retry_limit": 0,
    }
    data.update(overrides)
    return BackfillSettings.model_validate(data)


def polygon_request(**overrides: object) -> BackfillRequest:
    data: dict[str, object] = {
        "provider": BackfillProvider.POLYGON,
        "source_kind": BackfillSourceKind.AGGREGATES,
        "start_time": datetime(2024, 1, 2, tzinfo=UTC),
        "end_time": datetime(2024, 1, 4, tzinfo=UTC),
        "max_records": 100,
        "mode": BackfillMode.DRY_RUN,
        "resume": False,
        "polygon": PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            venue="XNAS",
            multiplier=1,
            timespan="minute",
            adjusted=True,
        ),
    }
    data.update(overrides)
    return BackfillRequest.model_validate(data)


class FakeBackfillSource:
    """Deterministic in-memory BackfillSource for engine tests."""

    def __init__(
        self,
        events_by_slice: dict[str, Sequence[CanonicalMarketEvent]] | None = None,
        *,
        may_have_more_slices: set[str] | None = None,
        slices: Sequence[BackfillSlice] | None = None,
        raise_on_fetch: Exception | None = None,
    ) -> None:
        self.events_by_slice = {k: list(v) for k, v in (events_by_slice or {}).items()}
        self.may_have_more_slices = may_have_more_slices or set()
        self._slices = list(slices) if slices is not None else None
        self.raise_on_fetch = raise_on_fetch
        self.fetch_calls: list[str] = []
        self.closed = False

    def build_slices(self, request: BackfillRequest) -> Sequence[BackfillSlice]:
        if self._slices is not None:
            return list(self._slices)
        from app.market_data.backfill.slicing import build_slices

        settings = BackfillSettings(
            enabled=True,
            checkpoint_enabled=False,
            max_slices=366,
        )
        return build_slices(request, settings)

    async def fetch_slice(
        self,
        slice_: BackfillSlice,
        request: BackfillRequest,
    ) -> tuple[Sequence[CanonicalMarketEvent], bool, int, dict[str, str]]:
        _ = request
        if self.closed:
            raise RuntimeError("source closed")
        self.fetch_calls.append(slice_.slice_id)
        if self.raise_on_fetch is not None:
            raise self.raise_on_fetch
        events = self.events_by_slice.get(slice_.slice_id, [])
        may_have_more = slice_.slice_id in self.may_have_more_slices
        return list(events), may_have_more, 1, {"slice_id": slice_.slice_id}

    async def aclose(self) -> None:
        self.closed = True


def build_engine(
    tmp_path: Path,
    source: FakeBackfillSource,
    *,
    clock: FixedClock | None = None,
    settings: BackfillSettings | None = None,
    provider: BackfillProvider = BackfillProvider.POLYGON,
    source_kind: BackfillSourceKind = BackfillSourceKind.AGGREGATES,
) -> tuple[BackfillEngine, FileBackfillCheckpointStore, FixedClock]:
    resolved_clock = clock or FixedClock(T0)
    resolved_settings = settings or backfill_settings(tmp_path)
    store = FileBackfillCheckpointStore(resolved_settings.checkpoint_directory)  # type: ignore[arg-type]
    engine = build_backfill_engine(
        resolved_settings,
        clock=resolved_clock,
        source_registry=StaticSourceRegistry(sources={(provider.value, source_kind.value): source}),
        checkpoint_store=store,
        sleeper=NoOpBackfillSleeper(),
    )
    return engine, store, resolved_clock


def two_day_bar_source() -> FakeBackfillSource:
    """Two calendar-day slices with one bar each (stable idempotency keys)."""
    day0 = "day-0000-2024-01-02"
    day1 = "day-0001-2024-01-03"
    t0 = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    t1 = datetime(2024, 1, 3, 15, 0, tzinfo=UTC)
    b0 = make_bar(
        occurred_at=t0,
        effective_at=t0,
        known_at=t0 + timedelta(milliseconds=50),
        ingested_at=t0 + timedelta(seconds=1),
        close_time=t0,
        window_start=t0 - timedelta(minutes=1),
        window_end=t0,
        source=make_bar().source.model_copy(update={"source_event_id": "bar-d0"}),
    )
    b1 = make_bar(
        occurred_at=t1,
        effective_at=t1,
        known_at=t1 + timedelta(milliseconds=50),
        ingested_at=t1 + timedelta(seconds=1),
        close_time=t1,
        window_start=t1 - timedelta(minutes=1),
        window_end=t1,
        source=make_bar().source.model_copy(update={"source_event_id": "bar-d1"}),
    )
    return FakeBackfillSource(
        events_by_slice={day0: [b0], day1: [b1]},
    )


def event_keys(events: Sequence[CanonicalMarketEvent]) -> list[str]:
    return [build_idempotency_key(e) for e in events]


def day_range(start: datetime, days: int) -> tuple[datetime, datetime]:
    return start, start + timedelta(days=days)
