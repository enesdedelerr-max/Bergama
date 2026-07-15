"""Deterministic Backfill slice builders (#309)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.backfill_settings import BackfillSettings
from app.market_data.backfill.errors import BackfillSliceBuildError, BackfillUnboundedRequestError
from app.market_data.backfill.models import (
    BackfillCapability,
    BackfillProvider,
    BackfillRequest,
    BackfillSlice,
    BackfillSourceKind,
)


def build_slices(request: BackfillRequest, settings: BackfillSettings) -> list[BackfillSlice]:
    """Build deterministic non-overlapping slices for one provider/source."""
    capability = request.capability()
    if capability is BackfillCapability.BOUNDED_REFRESH:
        return [
            BackfillSlice(
                slice_id="refresh-0",
                start_time=request.start_time,
                end_time=request.end_time,
                provider_cursor={},
                status="pending",
            )
        ]

    if request.provider is BackfillProvider.POLYGON:
        assert request.polygon is not None
        if request.polygon.timespan in {"minute", "hour"}:
            return _calendar_day_slices(request, settings)
        return _calendar_month_slices(request, settings)

    if request.provider is BackfillProvider.FRED:
        days = max(1, settings.default_slice_days)
        return _fixed_day_slices(request, settings, day_width=days)

    if request.provider is BackfillProvider.BENZINGA:
        return _calendar_day_slices(request, settings)

    raise BackfillSliceBuildError(
        detail=f"no slicer for {request.provider.value}/{request.source_kind.value}"
    )


def _calendar_day_slices(
    request: BackfillRequest,
    settings: BackfillSettings,
) -> list[BackfillSlice]:
    start = request.start_time.astimezone(UTC)
    end = request.end_time.astimezone(UTC)
    cursor = datetime(start.year, start.month, start.day, tzinfo=UTC)
    slices: list[BackfillSlice] = []
    index = 0
    while cursor < end:
        nxt = cursor + timedelta(days=1)
        slice_start = max(cursor, start)
        slice_end = min(nxt, end)
        if slice_start < slice_end:
            slices.append(
                BackfillSlice(
                    slice_id=f"day-{index:04d}-{cursor.date().isoformat()}",
                    start_time=slice_start,
                    end_time=slice_end,
                )
            )
            index += 1
        if len(slices) > settings.max_slices:
            raise BackfillUnboundedRequestError(
                detail=f"slice count exceeds max_slices={settings.max_slices}"
            )
        cursor = nxt
    if not slices:
        raise BackfillSliceBuildError(detail="no slices produced for range")
    if len(slices) > settings.max_slices:
        raise BackfillUnboundedRequestError(
            detail=f"slice count exceeds max_slices={settings.max_slices}"
        )
    return slices


def _calendar_month_slices(
    request: BackfillRequest,
    settings: BackfillSettings,
) -> list[BackfillSlice]:
    start = request.start_time.astimezone(UTC)
    end = request.end_time.astimezone(UTC)
    year, month = start.year, start.month
    slices: list[BackfillSlice] = []
    index = 0
    while True:
        month_start = datetime(year, month, 1, tzinfo=UTC)
        # Exclusive end: first day of next month
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=UTC)
        slice_start = max(month_start, start)
        slice_end = min(next_month, end)
        if slice_start < slice_end:
            slices.append(
                BackfillSlice(
                    slice_id=f"month-{index:04d}-{year:04d}-{month:02d}",
                    start_time=slice_start,
                    end_time=slice_end,
                )
            )
            index += 1
        if len(slices) > settings.max_slices:
            raise BackfillUnboundedRequestError(
                detail=f"slice count exceeds max_slices={settings.max_slices}"
            )
        if next_month >= end:
            break
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    if not slices:
        raise BackfillSliceBuildError(detail="no slices produced for range")
    return slices


def _fixed_day_slices(
    request: BackfillRequest,
    settings: BackfillSettings,
    *,
    day_width: int,
) -> list[BackfillSlice]:
    start = request.start_time.astimezone(UTC)
    end = request.end_time.astimezone(UTC)
    cursor = start
    slices: list[BackfillSlice] = []
    index = 0
    while cursor < end:
        nxt = min(cursor + timedelta(days=day_width), end)
        slices.append(
            BackfillSlice(
                slice_id=f"window-{index:04d}",
                start_time=cursor,
                end_time=nxt,
            )
        )
        index += 1
        if len(slices) > settings.max_slices:
            raise BackfillUnboundedRequestError(
                detail=f"slice count exceeds max_slices={settings.max_slices}"
            )
        cursor = nxt
    if not slices:
        raise BackfillSliceBuildError(detail="no slices produced for range")
    return slices


def assert_contiguous_no_overlap(slices: list[BackfillSlice]) -> None:
    """Test/helper invariant check for historical slices."""
    if not slices:
        return
    ordered = sorted(slices, key=lambda s: (s.start_time, s.end_time, s.slice_id))
    for left, right in zip(ordered, ordered[1:], strict=False):
        if right.start_time < left.end_time:
            raise BackfillSliceBuildError(detail="slice overlap detected")
        if right.start_time > left.end_time:
            # Gaps are not allowed for historical contiguous policies.
            raise BackfillSliceBuildError(detail="slice gap detected")


# Silence unused import if SourceKind referenced only in docs.
_ = BackfillSourceKind
