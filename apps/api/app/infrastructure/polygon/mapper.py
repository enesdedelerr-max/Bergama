"""Map Polygon aggregate bars to canonical BarEvent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.clock import Clock
from app.infrastructure.polygon.errors import PolygonMappingFailedError
from app.infrastructure.polygon.schemas import PolygonAggBar, PolygonAggsResponse
from app.market_data.enums import AdjustmentState
from app.market_data.events.bar import BarEvent
from app.market_data.identity import InstrumentId
from app.market_data.money import require_finite_decimal
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

# Explicit #302 daily-bar policy (not exchange-session close).
DAILY_WINDOW_POLICY = "utc_fixed_24h_from_provider_t"


def timespan_duration(*, timespan: str, multiplier: int) -> timedelta:
    """Exact duration for minute/hour bars."""
    if timespan == "minute":
        return timedelta(minutes=multiplier)
    if timespan == "hour":
        return timedelta(hours=multiplier)
    if timespan == "day":
        # Explicit fixed 24h from provider t — documented limitation vs NYSE RTH.
        return timedelta(days=multiplier)
    msg = f"unsupported timespan {timespan!r}"
    raise PolygonMappingFailedError(msg)


def ms_to_utc(timestamp_ms: int) -> datetime:
    try:
        seconds, millis = divmod(int(timestamp_ms), 1000)
        return datetime.fromtimestamp(seconds, tz=UTC) + timedelta(milliseconds=millis)
    except (OverflowError, OSError, ValueError, TypeError) as exc:
        raise PolygonMappingFailedError("invalid polygon bar timestamp") from exc


def decimal_from_provider(value: float | int | str, *, field_name: str) -> Decimal:
    # Convert via str to avoid float binary residue where possible.
    return require_finite_decimal(str(value), field_name=field_name)


def map_adjustment(*, adjusted: bool | None, requested_adjusted: bool) -> AdjustmentState:
    flag = requested_adjusted if adjusted is None else adjusted
    return AdjustmentState.SPLIT_ADJUSTED if flag else AdjustmentState.UNADJUSTED


def map_bar_event(
    bar: PolygonAggBar,
    *,
    response: PolygonAggsResponse,
    instrument: InstrumentId,
    currency: str,
    venue: str | None,
    timespan: str,
    multiplier: int,
    requested_adjusted: bool,
    known_at: datetime,
    clock: Clock,
    endpoint_ref: str,
    bar_index: int,
    request_symbol: str,
) -> BarEvent:
    try:
        window_start = ms_to_utc(bar.timestamp_ms)
        duration = timespan_duration(timespan=timespan, multiplier=multiplier)
        window_end = window_start + duration
        close_time = window_end
        ingested_at = clock.now()
        if known_at.tzinfo is None:
            raise PolygonMappingFailedError("known_at must be timezone-aware")

        # #301: known_at > ingested_at requires is_late (late observation / clock skew).
        quality = DataQualityFlags()
        if known_at > ingested_at:
            lag_ms = int((known_at - ingested_at).total_seconds() * 1000)
            quality = DataQualityFlags(is_late=True, late_arrival_lag_ms=max(lag_ms, 0))

        open_ = decimal_from_provider(bar.open, field_name="open")
        high = decimal_from_provider(bar.high, field_name="high")
        low = decimal_from_provider(bar.low, field_name="low")
        close = decimal_from_provider(bar.close, field_name="close")
        volume = decimal_from_provider(bar.volume, field_name="volume")
        vwap = decimal_from_provider(bar.vwap, field_name="vwap") if bar.vwap is not None else None

        # Provider ticker only in SourceReference — never derive InstrumentId/currency.
        polygon_symbol = (response.ticker or request_symbol).strip() or request_symbol
        source_event_id = f"{response.request_id or 'noreq'}:{bar.timestamp_ms}:{bar_index}"
        extras: dict[str, str] = {
            "adjusted": str(
                response.adjusted if response.adjusted is not None else requested_adjusted
            ).lower(),
            "status": response.status or "",
            "timespan": timespan,
            "multiplier": str(multiplier),
            "endpoint": "stocks.v2.aggs",
            "provider_window_start_ms": str(bar.timestamp_ms),
        }
        if timespan == "day":
            extras["window_policy"] = DAILY_WINDOW_POLICY
        if bar.otc is True:
            extras["otc"] = "true"

        source = SourceReference(
            provider="polygon",
            source_symbol=polygon_symbol,
            source_event_id=source_event_id,
            source_payload_ref=endpoint_ref,
            extras={k: v for k, v in extras.items() if v != ""},
        )

        return BarEvent(
            schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
            instrument=instrument,
            source=source,
            quality=quality,
            adjustment_state=map_adjustment(
                adjusted=response.adjusted,
                requested_adjusted=requested_adjusted,
            ),
            occurred_at=close_time,
            effective_at=window_start,
            known_at=known_at,
            ingested_at=ingested_at,
            currency=currency,
            venue=venue,
            window_start=window_start,
            window_end=window_end,
            close_time=close_time,
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            vwap=vwap,
            trade_count=bar.transactions,
            metadata={},
        )
    except PolygonMappingFailedError:
        raise
    except Exception as exc:
        raise PolygonMappingFailedError("failed to map polygon bar") from exc
