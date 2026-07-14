"""Synthetic FRED fixtures mapped to canonical events."""

from __future__ import annotations

from datetime import datetime

from app.infrastructure.fred.mapper import map_observation_event
from app.infrastructure.fred.schemas import FredObservation
from app.market_data.events.macro import MacroEvent
from app.market_data.identity import InstrumentId
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.provider_contracts.identities import macro_instrument

FRED_SERIES_ID = "GDP"
CANONICAL_SERIES_ID = "us.gdp"


def macro_observation(
    *,
    instrument: InstrumentId | None = None,
    obs_date: str = "2024-01-01",
    realtime_start: str = "2024-01-31",
    realtime_end: str = "9999-12-31",
    value: str = "12345.6",
    ingested_at: datetime | None = None,
) -> MacroEvent:
    observation = FredObservation.model_validate(
        {
            "realtime_start": realtime_start,
            "realtime_end": realtime_end,
            "date": obs_date,
            "value": value,
        }
    )
    event = map_observation_event(
        observation,
        instrument=instrument or macro_instrument(),
        canonical_series_id=CANONICAL_SERIES_ID,
        fred_series_id=FRED_SERIES_ID,
        series_meta=None,
        ingested_at=ingested_at or OBSERVED_AT,
    )
    assert event is not None
    return event


def missing_observation(
    *,
    instrument: InstrumentId | None = None,
    ingested_at: datetime | None = None,
) -> MacroEvent | None:
    observation = FredObservation.model_validate(
        {
            "realtime_start": "2024-01-31",
            "realtime_end": "9999-12-31",
            "date": "2024-01-01",
            "value": ".",
        }
    )
    return map_observation_event(
        observation,
        instrument=instrument or macro_instrument(),
        canonical_series_id=CANONICAL_SERIES_ID,
        fred_series_id=FRED_SERIES_ID,
        series_meta=None,
        ingested_at=ingested_at or OBSERVED_AT,
    )
