"""Previous-close / current-open selection and gap math."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.market_data.events.bar import BarEvent
from app.premarket.errors import (
    GapAmbiguousSelectionError,
    GapMissingBarError,
    GapStaleKnownAtError,
    GapZeroCloseError,
)
from app.premarket.gap.policy import (
    GAP_DIRECTION_DOWN,
    GAP_DIRECTION_FLAT,
    GAP_DIRECTION_UP,
    GAP_PERCENT_QUANTUM,
    GAP_PERCENT_ROUNDING,
    SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
)


@dataclass(frozen=True, slots=True)
class SelectedGapPrices:
    """Deterministic prior-close / current-open pair for one instrument."""

    instrument_key: str
    previous_bar: BarEvent
    current_bar: BarEvent
    previous_session_close: Decimal
    current_session_open: Decimal
    gap_percent: Decimal
    gap_direction: str


def assert_bars_known_at_or_before(bars: tuple[BarEvent, ...], *, as_of: datetime) -> None:
    """Fail closed when any bar is known after ``as_of``."""
    for bar in bars:
        if bar.known_at > as_of:
            raise GapStaleKnownAtError(
                detail=(
                    f"known_at_after_as_of:"
                    f"{bar.source.source_event_id or bar.instrument.instrument_key}"
                )
            )


def select_gap_prices_for_instrument(
    *,
    instrument_key: str,
    bars: tuple[BarEvent, ...],
    as_of: datetime,
    selection_policy_id: str,
) -> SelectedGapPrices:
    """Select previous close and current open under the pinned v1 policy."""
    if selection_policy_id != SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1:
        raise GapAmbiguousSelectionError(detail=f"unsupported_selection:{selection_policy_id}")

    eligible = [
        bar
        for bar in bars
        if bar.instrument.instrument_key == instrument_key and bar.close_time <= as_of
    ]
    if len(eligible) < 2:
        raise GapMissingBarError(detail=f"insufficient_bars:{instrument_key}:{len(eligible)}")

    ordered = sorted(
        eligible,
        key=lambda bar: (
            bar.close_time,
            bar.source.source_event_id or "",
            bar.source.provider,
        ),
    )
    # Detect ambiguous duplicate close_time + source_event_id pairs.
    seen_keys: set[tuple[datetime, str, str]] = set()
    for bar in ordered:
        key = (bar.close_time, bar.source.source_event_id or "", bar.source.provider)
        if key in seen_keys:
            raise GapAmbiguousSelectionError(
                detail=f"duplicate_bar_key:{instrument_key}:{bar.close_time.isoformat()}"
            )
        seen_keys.add(key)

    previous_bar = ordered[-2]
    current_bar = ordered[-1]
    previous_close = previous_bar.close
    current_open = current_bar.open
    if previous_close <= 0:
        raise GapZeroCloseError(detail=f"non_positive_previous_close:{instrument_key}")

    raw_gap = (current_open - previous_close) / previous_close
    gap_percent = raw_gap.quantize(GAP_PERCENT_QUANTUM, rounding=GAP_PERCENT_ROUNDING)
    if gap_percent > 0:
        direction = GAP_DIRECTION_UP
    elif gap_percent < 0:
        direction = GAP_DIRECTION_DOWN
    else:
        direction = GAP_DIRECTION_FLAT

    return SelectedGapPrices(
        instrument_key=instrument_key,
        previous_bar=previous_bar,
        current_bar=current_bar,
        previous_session_close=previous_close,
        current_session_open=current_open,
        gap_percent=gap_percent,
        gap_direction=direction,
    )
