"""Map FRED REST responses to #301 MacroEvent (Issue #304B)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger, structured_extra
from app.infrastructure.fred.errors import FredMappingFailedError
from app.infrastructure.fred.schemas import FredObservation, FredSeries
from app.market_data.enums import AdjustmentState
from app.market_data.events.macro import MacroEvent
from app.market_data.identity import InstrumentId
from app.market_data.money import require_finite_decimal
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

logger = get_logger(__name__)

PROVIDER_SCHEMA_VERSION = "v1"
MISSING_VALUE_MARKER = "."
OBSERVATION_DATE_POLICY = "fred_observation_date_as_utc_midnight"
KNOWN_AT_POLICY = "fred_realtime_start_as_utc_midnight"

# Explicit closed frequency map — only the issue-supported canonical set.
FREQUENCY_DEFINITIONS: dict[str, str] = {
    "d": "daily",
    "daily": "daily",
    "w": "weekly",
    "weekly": "weekly",
    "m": "monthly",
    "monthly": "monthly",
    "q": "quarterly",
    "quarterly": "quarterly",
    "a": "annual",
    "annual": "annual",
}

# Frequencies promoted to MacroEvent.frequency.
CANONICAL_FREQUENCIES: frozenset[str] = frozenset(FREQUENCY_DEFINITIONS.values())


@dataclass(frozen=True, slots=True)
class MapObservationResult:
    events: tuple[MacroEvent, ...]
    skipped_missing: int


class SeriesMetadataView(BaseModel):
    """Safe, mapped series metadata for callers (not a #301 event)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fred_series_id: str = Field(min_length=1, max_length=64)
    title: str | None = None
    frequency: str | None = None
    frequency_raw: str | None = None
    units_raw: str | None = None
    seasonal_adjustment: str | None = None
    observation_start: str | None = None
    observation_end: str | None = None
    last_updated: str | None = None
    notes: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


def parse_fred_date(value: str, *, field_name: str) -> date:
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise FredMappingFailedError(f"invalid {field_name} date {text!r}") from exc


def utc_midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def map_frequency(
    *,
    frequency: str | None,
    frequency_short: str | None,
) -> tuple[str | None, str | None]:
    """Return (canonical_or_none, raw_provider_text)."""
    raw_candidates = [frequency_short, frequency]
    raw = next((c.strip() for c in raw_candidates if c and c.strip()), None)
    if raw is None:
        return None, None
    mapped = FREQUENCY_DEFINITIONS.get(raw.lower())
    if mapped is None:
        return None, raw
    if mapped not in CANONICAL_FREQUENCIES:
        return None, raw
    return mapped, raw


def decimal_from_fred(value: str, *, field_name: str) -> Decimal:
    return require_finite_decimal(value, field_name=field_name)


def _bound(value: str | None, *, limit: int = 512) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:limit]


def map_series_metadata(series: FredSeries) -> SeriesMetadataView:
    freq, raw_freq = map_frequency(
        frequency=series.frequency,
        frequency_short=series.frequency_short,
    )
    attributes: dict[str, str] = {}
    for key, raw in (
        ("fred_series_id", series.id),
        ("title", series.title),
        ("frequency", series.frequency),
        ("frequency_short", series.frequency_short),
        ("units", series.units),
        ("units_short", series.units_short),
        ("seasonal_adjustment", series.seasonal_adjustment),
        ("seasonal_adjustment_short", series.seasonal_adjustment_short),
        ("observation_start", series.observation_start),
        ("observation_end", series.observation_end),
        ("realtime_start", series.realtime_start),
        ("realtime_end", series.realtime_end),
        ("last_updated", series.last_updated),
    ):
        text = _bound(raw)
        if text is not None:
            attributes[key] = text
    notes = _bound(series.notes)
    if notes is not None:
        attributes["notes"] = notes
    return SeriesMetadataView(
        fred_series_id=series.id.strip(),
        title=_bound(series.title),
        frequency=freq,
        frequency_raw=raw_freq,
        units_raw=_bound(series.units),
        seasonal_adjustment=_bound(series.seasonal_adjustment),
        observation_start=_bound(series.observation_start, limit=32),
        observation_end=_bound(series.observation_end, limit=32),
        last_updated=_bound(series.last_updated, limit=64),
        notes=notes,
        attributes=attributes,
    )


def map_observation_event(
    observation: FredObservation,
    *,
    instrument: InstrumentId,
    canonical_series_id: str,
    fred_series_id: str,
    series_meta: SeriesMetadataView | None,
    ingested_at: datetime,
) -> MacroEvent | None:
    raw_value = observation.value.strip()
    if raw_value == MISSING_VALUE_MARKER:
        logger.warning(
            "fred missing observation value skipped",
            extra=structured_extra(
                event="fred.observation.missing_skipped",
                source="fred_mapper",
                fred_series_id=fred_series_id[:64],
                observation_date=observation.date[:32],
            ),
        )
        return None

    try:
        value = decimal_from_fred(raw_value, field_name="value")
    except ValueError as exc:
        raise FredMappingFailedError(
            f"invalid value for observation date={observation.date}"
        ) from exc

    obs_day = parse_fred_date(observation.date, field_name="date")
    known_day = parse_fred_date(observation.realtime_start, field_name="realtime_start")
    effective_at = utc_midnight(obs_day)
    occurred_at = effective_at
    known_at = utc_midnight(known_day)

    if occurred_at > known_at:
        # Official vintages can theoretically be awkward; fail closed rather than invent PIT.
        raise FredMappingFailedError(
            f"occurred_at > known_at for date={observation.date} "
            f"realtime_start={observation.realtime_start}"
        )

    # Declare late/clock-skew semantics; preserve true realtime_start as known_at.
    quality = DataQualityFlags(is_late=True) if known_at > ingested_at else DataQualityFlags()

    rt_end = observation.realtime_end.strip()
    source_event_id = (
        f"{fred_series_id}:{observation.date}:{observation.realtime_start}:{rt_end}"
    )[:256]

    metadata: dict[str, str] = {
        "fred_observation_date": observation.date[:32],
        "fred_realtime_start": observation.realtime_start[:32],
        "fred_realtime_end": rt_end[:32],
        "observation_date_policy": OBSERVATION_DATE_POLICY,
        "known_at_policy": KNOWN_AT_POLICY,
    }
    if series_meta is not None:
        if series_meta.title:
            metadata["fred_title"] = series_meta.title[:512]
        if series_meta.units_raw:
            metadata["fred_units"] = series_meta.units_raw[:512]
        if series_meta.seasonal_adjustment:
            metadata["fred_seasonal_adjustment"] = series_meta.seasonal_adjustment[:128]
        if series_meta.frequency_raw and series_meta.frequency is None:
            metadata["fred_frequency_raw"] = series_meta.frequency_raw[:64]

    frequency = series_meta.frequency if series_meta is not None else None

    return MacroEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument,
        source=SourceReference(
            provider="fred",
            source_symbol=fred_series_id[:128],
            source_event_id=source_event_id,
            extras={
                "endpoint": "fred/series/observations",
                "provider_schema_version": PROVIDER_SCHEMA_VERSION,
                "fred_series_id": fred_series_id[:64],
            },
        ),
        quality=quality,
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=occurred_at,
        effective_at=effective_at,
        known_at=known_at,
        ingested_at=ingested_at,
        currency=None,
        venue=None,
        series_id=canonical_series_id[:64],
        value=value,
        unit=None,  # never invent; FRED units preserved in metadata
        frequency=frequency,
        metadata=metadata,
    )


def map_observation_events(
    observations: list[FredObservation],
    *,
    instrument: InstrumentId,
    canonical_series_id: str,
    fred_series_id: str,
    series_meta: SeriesMetadataView | None,
    ingested_at: datetime,
) -> MapObservationResult:
    events: list[MacroEvent] = []
    skipped = 0
    # Deterministic order: date, then realtime_start, then realtime_end.
    ordered = sorted(
        observations,
        key=lambda o: (o.date, o.realtime_start, o.realtime_end),
    )
    for observation in ordered:
        event = map_observation_event(
            observation,
            instrument=instrument,
            canonical_series_id=canonical_series_id,
            fred_series_id=fred_series_id,
            series_meta=series_meta,
            ingested_at=ingested_at,
        )
        if event is None:
            skipped += 1
            continue
        events.append(event)
    return MapObservationResult(events=tuple(events), skipped_missing=skipped)
