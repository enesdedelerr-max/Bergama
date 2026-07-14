"""FRED series observations → MacroEvent connector (Issue #304B)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.infrastructure.fred.errors import (
    FredAuthenticationFailedError,
    FredForbiddenError,
    FredInvalidRequestError,
    FredInvalidResponseError,
    FredMappingFailedError,
    FredNotConfiguredError,
    FredNotFoundError,
    FredProviderError,
)
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.mapper import (
    SeriesMetadataView,
    map_observation_events,
)
from app.infrastructure.fred.pagination import OffsetPaginationGuard
from app.infrastructure.fred.schemas import FredObservationsResponse
from app.market_data.events.macro import MacroEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)


class ObservationsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fred_series_id: str = Field(min_length=1, max_length=64)
    series_id: str = Field(
        min_length=1,
        max_length=64,
        description="Caller-supplied canonical MacroEvent.series_id",
    )
    instrument: InstrumentId
    observation_start: str | None = Field(default=None, min_length=10, max_length=10)
    observation_end: str | None = Field(default=None, min_length=10, max_length=10)
    realtime_start: str | None = Field(default=None, min_length=10, max_length=10)
    realtime_end: str | None = Field(default=None, min_length=10, max_length=10)
    sort_order: Literal["asc", "desc"] = "asc"
    output_type: Literal[1, 2, 3, 4] = 1
    series_meta: SeriesMetadataView | None = None

    @field_validator("fred_series_id")
    @classmethod
    def normalize_fred_id(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "fred_series_id must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("series_id")
    @classmethod
    def normalize_canonical_id(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "series_id must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator(
        "observation_start",
        "observation_end",
        "realtime_start",
        "realtime_end",
    )
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if len(text) != 10 or text[4] != "-" or text[7] != "-":
            msg = "date bounds must be YYYY-MM-DD"
            raise ValueError(msg)
        return text


class ObservationsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    events: tuple[MacroEvent, ...]
    pages_fetched: int
    skipped_missing: int
    fred_series_id: str
    series_id: str
    endpoint_refs: tuple[str, ...]


class FredObservationsConnector:
    """Fetch /fred/series/observations and map to MacroEvent with offset pagination."""

    def __init__(self, http: FredHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_observations(self, request: ObservationsRequest) -> ObservationsResult:
        if not self._http.settings.enabled:
            raise FredNotConfiguredError("fred is disabled")

        settings = self._http.settings
        guard = OffsetPaginationGuard(max_pages=settings.max_pages)
        events: list[MacroEvent] = []
        skipped = 0
        endpoint_refs: list[str] = []
        offset = 0
        limit = settings.max_results_per_page

        while True:
            guard.begin_page(offset)
            ingested_at = self._clock.now()
            params: dict[str, object] = {
                "series_id": request.fred_series_id,
                "limit": limit,
                "offset": offset,
                "sort_order": request.sort_order,
                "output_type": request.output_type,
                "units": "lin",
            }
            if request.observation_start is not None:
                params["observation_start"] = request.observation_start
            if request.observation_end is not None:
                params["observation_end"] = request.observation_end
            if request.realtime_start is not None:
                params["realtime_start"] = request.realtime_start
            if request.realtime_end is not None:
                params["realtime_end"] = request.realtime_end

            response = await self._http.get("/fred/series/observations", params=params)
            self._raise_for_status(response.status_code)
            endpoint_refs.append(
                self._http.sanitized_request_url(
                    "/fred/series/observations",
                    self._http.build_params(params),
                )
            )

            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise FredInvalidResponseError("fred observations response must be an object")
                parsed = FredObservationsResponse.model_validate(payload)
            except FredInvalidResponseError:
                raise
            except Exception as exc:
                raise FredInvalidResponseError("invalid fred observations response") from exc

            if parsed.offset != offset:
                raise FredInvalidResponseError(
                    f"fred observations offset mismatch request={offset} response={parsed.offset}"
                )

            try:
                mapped = map_observation_events(
                    parsed.observations,
                    instrument=request.instrument,
                    canonical_series_id=request.series_id,
                    fred_series_id=request.fred_series_id,
                    series_meta=request.series_meta,
                    ingested_at=ingested_at,
                )
            except FredMappingFailedError:
                raise
            except Exception as exc:
                raise FredMappingFailedError("failed to map fred observations") from exc

            events.extend(mapped.events)
            skipped += mapped.skipped_missing

            next_offset = offset + len(parsed.observations)
            if next_offset >= parsed.count or len(parsed.observations) == 0:
                break
            if len(parsed.observations) < limit and next_offset < parsed.count:
                # Provider returned a short page before count exhausted — fail closed.
                raise FredInvalidResponseError(
                    "fred observations short page before count exhausted"
                )
            offset = next_offset

        logger.info(
            "fred observations fetched",
            extra=structured_extra(
                event="fred.observations.fetched",
                source="fred_observations",
                series_id=request.series_id,
                fred_series_id=request.fred_series_id,
                event_count=len(events),
                skipped_missing=skipped,
                pages_fetched=guard.pages_fetched,
            ),
        )
        return ObservationsResult(
            events=tuple(events),
            pages_fetched=guard.pages_fetched,
            skipped_missing=skipped,
            fred_series_id=request.fred_series_id,
            series_id=request.series_id,
            endpoint_refs=tuple(endpoint_refs),
        )

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 400:
            raise FredInvalidRequestError("fred invalid request")
        if status_code == 401:
            raise FredAuthenticationFailedError("fred authentication failed")
        if status_code == 403:
            raise FredForbiddenError("fred forbidden")
        if status_code == 404:
            raise FredNotFoundError("fred not found")
        raise FredProviderError(f"fred provider error status={status_code}")
