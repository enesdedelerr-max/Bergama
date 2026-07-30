"""Deterministic Premarket Gap Scanner engine."""

from __future__ import annotations

from datetime import datetime

from app.market_data.events.bar import BarEvent
from app.premarket.errors import (
    GapDuplicateInstrumentError,
    GapUnsupportedEventError,
    GapValidationError,
    PremarketDisabledError,
)
from app.premarket.gap.identity import build_gap_record_id
from app.premarket.gap.models import (
    GapCollection,
    GapConfig,
    GapProvenance,
    GapRecord,
    GapScanRequest,
)
from app.premarket.gap.normalize import coerce_bar_events
from app.premarket.gap.ordering import (
    ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    gap_sort_key,
)
from app.premarket.gap.select import (
    assert_bars_known_at_or_before,
    select_gap_prices_for_instrument,
)
from app.premarket.settings import PremarketSettings
from app.premarket.watchlist.models import Watchlist
from app.strategy.keys import strategy_sha256


def scan_gaps(
    request: GapScanRequest | object,
    *,
    settings: PremarketSettings | None = None,
) -> GapCollection:
    """Scan overnight gaps for Watchlist instruments using offline BarEvents.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, scanning runs for direct unit use.
    """
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    validated = _coerce_request(request)
    records = _scan_records(
        watchlist=validated.watchlist,
        bars=validated.bars,
        as_of=validated.as_of,
        config=validated.config,
    )
    ordered = tuple(sorted(records, key=gap_sort_key))
    provenance = GapProvenance(
        config_fingerprint=_config_fingerprint(validated.config),
        input_fingerprint=_input_fingerprint(validated),
        ordering_policy_id=validated.config.ordering_policy_id,
        selection_policy_id=validated.config.selection_policy_id,
        source_identifiers=tuple(record.gap_record_id for record in ordered),
    )
    return GapCollection(
        as_of=validated.as_of,
        records=ordered,
        provenance=provenance,
    )


def scan_gaps_from_parts(
    *,
    watchlist: Watchlist | object,
    bars: object,
    as_of: datetime,
    config: GapConfig | object | None = None,
    settings: PremarketSettings | None = None,
) -> GapCollection:
    """Convenience entrypoint that coerces bar sequences."""
    if not isinstance(as_of, datetime):
        raise GapValidationError(detail="invalid_as_of")
    resolved_watchlist = (
        watchlist if isinstance(watchlist, Watchlist) else Watchlist.model_validate(watchlist)
    )
    request = GapScanRequest(
        watchlist=resolved_watchlist,
        bars=coerce_bar_events(bars),
        as_of=as_of,
        config=(
            GapConfig()
            if config is None
            else (config if isinstance(config, GapConfig) else GapConfig.model_validate(config))
        ),
    )
    return scan_gaps(request, settings=settings)


def _coerce_request(request: object) -> GapScanRequest:
    if isinstance(request, GapScanRequest):
        return request
    try:
        return GapScanRequest.model_validate(request)
    except Exception as exc:
        raise GapValidationError(detail=f"invalid_request:{exc}") from exc


def _scan_records(
    *,
    watchlist: Watchlist,
    bars: tuple[BarEvent, ...],
    as_of: datetime,
    config: GapConfig,
) -> list[GapRecord]:
    for bar in bars:
        if not isinstance(bar, BarEvent):
            raise GapUnsupportedEventError(detail=f"unsupported_event_type:{type(bar).__name__}")

    assert_bars_known_at_or_before(bars, as_of=as_of)

    seen_instruments: set[str] = set()
    records_by_id: dict[str, GapRecord] = {}

    for entry in watchlist.entries:
        instrument_key = entry.instrument_key
        if instrument_key in seen_instruments:
            raise GapDuplicateInstrumentError(detail=f"duplicate_instrument:{instrument_key}")
        seen_instruments.add(instrument_key)

        selected = select_gap_prices_for_instrument(
            instrument_key=instrument_key,
            bars=bars,
            as_of=as_of,
            selection_policy_id=config.selection_policy_id,
        )
        record_id = build_gap_record_id(
            instrument_key=instrument_key,
            previous_session_close=selected.previous_session_close,
            current_session_open=selected.current_session_open,
            gap_percent=selected.gap_percent,
            as_of=as_of,
            selection_policy_id=config.selection_policy_id,
            previous_bar_close_time=selected.previous_bar.close_time,
            current_bar_close_time=selected.current_bar.close_time,
            previous_bar_source_event_id=selected.previous_bar.source.source_event_id,
            current_bar_source_event_id=selected.current_bar.source.source_event_id,
        )
        if record_id in records_by_id:
            continue

        records_by_id[record_id] = GapRecord(
            gap_record_id=record_id,
            instrument_key=instrument_key,
            local_symbol=entry.local_symbol,
            previous_session_close=selected.previous_session_close,
            current_session_open=selected.current_session_open,
            gap_percent=selected.gap_percent,
            gap_direction=selected.gap_direction,
            event_time=selected.current_bar.occurred_at,
            known_at=selected.current_bar.known_at,
            as_of=as_of,
            selection_policy_id=config.selection_policy_id,
            previous_bar_source_event_id=selected.previous_bar.source.source_event_id,
            current_bar_source_event_id=selected.current_bar.source.source_event_id,
        )

    return list(records_by_id.values())


def _config_fingerprint(config: GapConfig) -> str:
    return strategy_sha256(config.model_dump(mode="python"))


def _input_fingerprint(request: GapScanRequest) -> str:
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "bars": [bar.model_dump(mode="python") for bar in request.bars],
            "config": request.config.model_dump(mode="python"),
            "ordering_policy_id": ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
            "watchlist": request.watchlist.model_dump(mode="python"),
        }
    )
