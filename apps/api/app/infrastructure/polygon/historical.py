"""Polygon historical aggregate-bars connector (Issue #302)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.infrastructure.polygon.errors import (
    PolygonAuthenticationFailedError,
    PolygonForbiddenError,
    PolygonInvalidRequestError,
    PolygonInvalidResponseError,
    PolygonNotConfiguredError,
    PolygonNotFoundError,
    PolygonProviderError,
)
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.mapper import map_bar_event
from app.infrastructure.polygon.pagination import PaginationGuard, sanitize_url, validate_next_url
from app.infrastructure.polygon.schemas import PolygonAggsResponse
from app.market_data.events.bar import BarEvent
from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware

logger = get_logger(__name__)


class PolygonTimespan(StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class HistoricalBarsRequest(BaseModel):
    """Caller-supplied historical bars request (provider symbol + canonical context)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    currency: str = Field(min_length=3, max_length=3)
    venue: str | None = Field(default=None, max_length=32)
    multiplier: int = Field(default=1, ge=1, le=10_000)
    timespan: PolygonTimespan
    start: datetime
    end: datetime
    adjusted: bool | None = None
    sort: Literal["asc", "desc"] = "asc"
    limit: int | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        # Explicit policy: strip + uppercase (Polygon stocks tickers are case-sensitive
        # for some assets; equities are conventionally upper — document and apply upper).
        text = value.strip().upper()
        if not text:
            msg = "symbol must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "currency must be a 3-letter ISO code"
            raise ValueError(msg)
        return text

    @field_validator("venue")
    @classmethod
    def normalize_venue(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().upper()
        return text or None

    @field_validator("start", "end")
    @classmethod
    def utc_range(cls, value: datetime, info: Any) -> datetime:
        return require_utc_aware(value, field_name=str(info.field_name))

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.start > self.end:
            msg = "start must be <= end"
            raise ValueError(msg)
        return self


class HistoricalBarsResult(BaseModel):
    """Connector result: ordered canonical bars + safe request metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bars: tuple[BarEvent, ...]
    pages_fetched: int
    request_ids: tuple[str, ...]
    endpoint_refs: tuple[str, ...]


def _format_path_time(value: datetime) -> str:
    # Millisecond epoch is unambiguous for minute/hour/day range queries.
    return str(int(value.astimezone(UTC).timestamp() * 1000))


class PolygonHistoricalConnector:
    """Fetch stocks custom aggregate bars and map to canonical BarEvent."""

    def __init__(self, http: PolygonHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResult:
        settings = self._http.settings
        if not settings.enabled:
            raise PolygonNotConfiguredError("polygon is disabled")

        limit = request.limit if request.limit is not None else settings.max_results_per_page
        if limit < 1 or limit > settings.max_results_per_page:
            msg = f"limit must be between 1 and {settings.max_results_per_page}"
            raise PolygonInvalidRequestError(msg)

        adjusted = settings.default_adjusted if request.adjusted is None else request.adjusted
        path = (
            f"/v2/aggs/ticker/{request.symbol}/range/"
            f"{request.multiplier}/{request.timespan.value}/"
            f"{_format_path_time(request.start)}/{_format_path_time(request.end)}"
        )
        params: dict[str, str | int | bool] = {
            "adjusted": str(adjusted).lower(),
            "sort": request.sort,
            "limit": limit,
        }

        guard = PaginationGuard(max_pages=settings.max_pages)
        bars: list[BarEvent] = []
        request_ids: list[str] = []
        endpoint_refs: list[str] = []
        next_url: str | None = None
        known_at = self._clock.now()

        while True:
            if next_url is None:
                url = path
                call_params: dict[str, Any] | None = params
                guard.begin_page(f"{settings.base_url}{path}")
                endpoint_ref = sanitize_url(f"{settings.base_url}{path}")
            else:
                validated = validate_next_url(next_url=next_url, base_url=settings.base_url)
                guard.begin_page(validated)
                url = validated
                call_params = None
                endpoint_ref = sanitize_url(validated)

            response = await self._http.get(url, params=call_params)
            self._raise_for_status(response.status_code)
            try:
                payload = response.json()
                parsed = PolygonAggsResponse.model_validate(payload)
            except Exception as exc:
                raise PolygonInvalidResponseError("invalid polygon aggregates response") from exc

            if parsed.request_id:
                request_ids.append(parsed.request_id)
            endpoint_refs.append(endpoint_ref)

            # Preserve provider order; do not silently deduplicate.
            for index, bar in enumerate(parsed.results):
                bars.append(
                    map_bar_event(
                        bar,
                        response=parsed,
                        instrument=request.instrument,
                        currency=request.currency,
                        venue=request.venue,
                        timespan=request.timespan.value,
                        multiplier=request.multiplier,
                        requested_adjusted=adjusted,
                        known_at=known_at,
                        clock=self._clock,
                        endpoint_ref=endpoint_ref,
                        bar_index=index,
                        request_symbol=request.symbol,
                    )
                )

            if not parsed.next_url:
                break
            next_url = parsed.next_url

        logger.info(
            "polygon historical bars fetched",
            extra=structured_extra(
                event="polygon.historical.bars.fetched",
                source="polygon_historical",
                symbol=request.symbol,
                bar_count=len(bars),
                pages=guard.pages_fetched,
            ),
        )
        return HistoricalBarsResult(
            bars=tuple(bars),
            pages_fetched=guard.pages_fetched,
            request_ids=tuple(request_ids),
            endpoint_refs=tuple(endpoint_refs),
        )

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 400:
            raise PolygonInvalidRequestError("polygon invalid request")
        if status_code == 401:
            raise PolygonAuthenticationFailedError("polygon authentication failed")
        if status_code == 403:
            raise PolygonForbiddenError("polygon forbidden")
        if status_code == 404:
            raise PolygonNotFoundError("polygon not found")
        # 429/5xx should normally be exhausted by retry helper.
        raise PolygonProviderError(f"polygon provider error status={status_code}")
