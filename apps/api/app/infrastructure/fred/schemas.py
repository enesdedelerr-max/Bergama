"""Provider-specific FRED REST schemas (Issue #304B)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FredSeries(BaseModel):
    """One series object from GET /fred/series."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    title: str | None = None
    frequency: str | None = None
    frequency_short: str | None = None
    units: str | None = None
    units_short: str | None = None
    seasonal_adjustment: str | None = None
    seasonal_adjustment_short: str | None = None
    observation_start: str | None = None
    observation_end: str | None = None
    realtime_start: str | None = None
    realtime_end: str | None = None
    last_updated: str | None = None
    notes: str | None = None


class FredSeriesResponse(BaseModel):
    """Response envelope for GET /fred/series."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    realtime_start: str | None = None
    realtime_end: str | None = None
    seriess: list[FredSeries] = Field(default_factory=list)


class FredObservation(BaseModel):
    """One observation row from GET /fred/series/observations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    realtime_start: str
    realtime_end: str
    date: str
    value: str


class FredObservationsResponse(BaseModel):
    """Response envelope for GET /fred/series/observations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    realtime_start: str | None = None
    realtime_end: str | None = None
    observation_start: str | None = None
    observation_end: str | None = None
    units: str | None = None
    output_type: int | str | None = None
    file_type: str | None = None
    order_by: str | None = None
    sort_order: str | None = None
    count: int
    offset: int
    limit: int
    observations: list[FredObservation] = Field(default_factory=list)
