"""Unit tests for deterministic Backfill slicing (#309)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.backfill_settings import BackfillSettings
from app.market_data.backfill.errors import BackfillUnboundedRequestError
from app.market_data.backfill.models import (
    BackfillProvider,
    BackfillRequest,
    BackfillSourceKind,
    FinnhubRefreshSelector,
    FredSelector,
    PolygonSelector,
    SecRefreshSelector,
)
from app.market_data.backfill.slicing import assert_contiguous_no_overlap, build_slices
from tests.support.market_data_fixtures import instrument


def _settings(**overrides: object) -> BackfillSettings:
    data: dict[str, object] = {
        "enabled": True,
        "checkpoint_enabled": False,
        "max_slices": 366,
        "default_slice_days": 1,
    }
    data.update(overrides)
    return BackfillSettings.model_validate(data)


def test_polygon_minute_calendar_day_slices_no_gap_overlap() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.POLYGON,
        source_kind=BackfillSourceKind.AGGREGATES,
        start_time=datetime(2024, 1, 2, 12, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 4, 6, 0, tzinfo=UTC),
        max_records=100,
        polygon=PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            timespan="minute",
        ),
    )
    slices = build_slices(req, _settings())
    assert len(slices) == 3
    assert_contiguous_no_overlap(slices)
    assert slices[0].start_time == datetime(2024, 1, 2, 12, 0, tzinfo=UTC)
    assert slices[0].end_time == datetime(2024, 1, 3, tzinfo=UTC)
    assert slices[1].start_time == datetime(2024, 1, 3, tzinfo=UTC)
    assert slices[-1].end_time == datetime(2024, 1, 4, 6, 0, tzinfo=UTC)


def test_polygon_day_calendar_month_slices() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.POLYGON,
        source_kind=BackfillSourceKind.AGGREGATES,
        start_time=datetime(2024, 1, 15, tzinfo=UTC),
        end_time=datetime(2024, 3, 10, tzinfo=UTC),
        max_records=100,
        polygon=PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            timespan="day",
        ),
    )
    slices = build_slices(req, _settings())
    assert len(slices) == 3
    assert_contiguous_no_overlap(slices)
    assert "month-0000-2024-01" in slices[0].slice_id
    assert "month-0002-2024-03" in slices[2].slice_id


def test_fred_fixed_windows() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.FRED,
        source_kind=BackfillSourceKind.OBSERVATIONS,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 5, tzinfo=UTC),
        max_records=100,
        fred=FredSelector(
            fred_series_id="GDP",
            series_id="gdp",
            instrument=instrument(),
        ),
    )
    slices = build_slices(req, _settings(default_slice_days=2))
    assert len(slices) == 2
    assert_contiguous_no_overlap(slices)
    assert slices[0].end_time == datetime(2024, 1, 3, tzinfo=UTC)


def test_refresh_sources_single_slice() -> None:
    fh = BackfillRequest(
        provider=BackfillProvider.FINNHUB,
        source_kind=BackfillSourceKind.BOTH_REFRESH,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=5,
        finnhub=FinnhubRefreshSelector(
            ticker="AAPL",
            instrument=instrument(),
            refresh_type="both",
        ),
    )
    sec = BackfillRequest(
        provider=BackfillProvider.SEC,
        source_kind=BackfillSourceKind.RECENT_FILINGS,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=5,
        sec=SecRefreshSelector(cik="320193", instrument=instrument()),
    )
    assert len(build_slices(fh, _settings())) == 1
    assert build_slices(fh, _settings())[0].slice_id == "refresh-0"
    assert len(build_slices(sec, _settings())) == 1


def test_max_slices_enforced() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.POLYGON,
        source_kind=BackfillSourceKind.AGGREGATES,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 10, tzinfo=UTC),
        max_records=100,
        polygon=PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            timespan="minute",
        ),
    )
    with pytest.raises(BackfillUnboundedRequestError):
        build_slices(req, _settings(max_slices=3))
