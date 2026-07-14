"""Benzinga Newsfeed connector → NewsEvent (Issue #304D)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.infrastructure.benzinga.errors import (
    BenzingaAuthenticationFailedError,
    BenzingaEntitlementRequiredError,
    BenzingaInvalidRequestError,
    BenzingaInvalidResponseError,
    BenzingaMappingFailedError,
    BenzingaNotConfiguredError,
    BenzingaNotFoundError,
    BenzingaProviderError,
)
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.mapper import map_news_item
from app.infrastructure.benzinga.pagination import PagePaginationGuard
from app.infrastructure.benzinga.schemas import BenzingaNewsItem
from app.market_data.events.news import NewsEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)

_NEWS_PATH = "/api/v2/news"
_ALLOWED_SORT = frozenset(
    {
        "id:asc",
        "id:desc",
        "created:asc",
        "created:desc",
        "updated:asc",
        "updated:desc",
    }
)
_ALLOWED_DISPLAY = frozenset({"headline", "abstract"})


class NewsRequest(BaseModel):
    """Bounded news fetch request. Requires an official time/delta bound."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    date: str | None = Field(default=None, min_length=10, max_length=10)
    date_from: str | None = Field(default=None, min_length=10, max_length=10)
    date_to: str | None = Field(default=None, min_length=10, max_length=10)
    updated_since: int | None = Field(default=None, ge=0)
    published_since: int | None = Field(default=None, ge=0)
    tickers: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()
    page: int = Field(default=0, ge=0, le=100_000)
    page_size: int | None = Field(default=None, ge=1, le=100)
    sort: Literal[
        "id:asc",
        "id:desc",
        "created:asc",
        "created:desc",
        "updated:asc",
        "updated:desc",
    ] = "created:desc"
    display_output: Literal["headline", "abstract"] | None = None
    ticker_to_instrument: Mapping[str, InstrumentId] = Field(default_factory=dict)
    anchor_instrument: InstrumentId | None = None

    @field_validator("date", "date_from", "date_to")
    @classmethod
    def validate_ymd(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        try:
            date.fromisoformat(text)
        except ValueError as exc:
            msg = "date bounds must be YYYY-MM-DD"
            raise ValueError(msg) from exc
        return text

    @field_validator("tickers", "channels", mode="before")
    @classmethod
    def coerce_tuple(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, str):
            return tuple(p.strip() for p in value.split(",") if p.strip())
        return value

    @field_validator("display_output", mode="before")
    @classmethod
    def reject_full(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip().lower()
            if text == "full":
                msg = "display_output=full is rejected"
                raise ValueError(msg)
            if text not in _ALLOWED_DISPLAY:
                msg = "display_output must be 'headline' or 'abstract'"
                raise ValueError(msg)
            return text
        return value

    @model_validator(mode="after")
    def require_bound(self) -> NewsRequest:
        has_date = self.date is not None
        has_range = self.date_from is not None and self.date_to is not None
        has_partial_range = (self.date_from is None) != (self.date_to is None)
        if has_partial_range:
            msg = "date_from and date_to must be provided together"
            raise ValueError(msg)
        if not (
            has_date
            or has_range
            or self.updated_since is not None
            or self.published_since is not None
        ):
            msg = (
                "news request must be bounded by date, date_from/date_to, "
                "updated_since, or published_since"
            )
            raise ValueError(msg)
        if self.sort not in _ALLOWED_SORT:
            msg = "unsupported sort"
            raise ValueError(msg)
        return self


class NewsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    events: tuple[NewsEvent, ...]
    pages_fetched: int
    stories_seen: int
    may_have_more: bool
    endpoint_refs: tuple[str, ...]


class BenzingaNewsConnector:
    """Fetch /api/v2/news and map stories to NewsEvent with page pagination."""

    def __init__(self, http: BenzingaHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_news(self, request: NewsRequest) -> NewsResult:
        if not self._http.settings.enabled:
            raise BenzingaNotConfiguredError("benzinga is disabled")

        settings = self._http.settings
        page_size = request.page_size if request.page_size is not None else settings.page_size
        if page_size < 1 or page_size > 100:
            raise BenzingaInvalidRequestError("page_size must be between 1 and 100")

        display = request.display_output or settings.default_display_output
        if display not in _ALLOWED_DISPLAY:
            raise BenzingaInvalidRequestError("display_output must be headline or abstract")

        guard = PagePaginationGuard(max_pages=settings.max_pages)
        events: list[NewsEvent] = []
        endpoint_refs: list[str] = []
        stories_seen = 0
        page = request.page
        may_have_more = False

        while True:
            guard.begin_page(page)
            observed_at = self._clock.now()
            params: dict[str, object] = {
                "page": page,
                "pageSize": page_size,
                "sort": request.sort,
                "displayOutput": display,
            }
            if request.date is not None:
                params["date"] = request.date
            if request.date_from is not None:
                params["dateFrom"] = request.date_from
            if request.date_to is not None:
                params["dateTo"] = request.date_to
            if request.updated_since is not None:
                params["updatedSince"] = request.updated_since
            if request.published_since is not None:
                params["publishedSince"] = request.published_since
            if request.tickers:
                params["tickers"] = ",".join(request.tickers)
            if request.channels:
                params["channels"] = ",".join(request.channels)

            response = await self._http.get(_NEWS_PATH, params=params)
            self._raise_for_status(response.status_code)
            safe_params = self._http.build_params(params)
            endpoint_ref = self._http.sanitized_request_url(_NEWS_PATH, safe_params)
            endpoint_refs.append(endpoint_ref)

            try:
                payload = response.json()
            except Exception as exc:
                raise BenzingaInvalidResponseError("benzinga news response is not JSON") from exc

            if not isinstance(payload, list):
                raise BenzingaInvalidResponseError("benzinga news response must be an array")

            items: list[BenzingaNewsItem] = []
            for raw in payload:
                if not isinstance(raw, dict):
                    raise BenzingaInvalidResponseError("benzinga news item must be an object")
                try:
                    items.append(BenzingaNewsItem.model_validate(raw))
                except Exception as exc:
                    raise BenzingaInvalidResponseError("invalid benzinga news item") from exc

            stories_seen += len(items)
            for item in items:
                try:
                    mapped = map_news_item(
                        item,
                        ticker_to_instrument=request.ticker_to_instrument,
                        anchor_instrument=request.anchor_instrument,
                        observed_at=observed_at,
                        endpoint_ref=endpoint_ref,
                    )
                except BenzingaMappingFailedError:
                    raise
                except Exception as exc:
                    raise BenzingaMappingFailedError("failed to map benzinga news item") from exc
                events.extend(mapped)

            if len(items) < page_size:
                may_have_more = False
                break
            if guard.pages_fetched >= settings.max_pages:
                may_have_more = True
                break
            page += 1

        logger.info(
            "benzinga news fetched",
            extra=structured_extra(
                event="benzinga.news.fetched",
                source="benzinga_news",
                event_count=len(events),
                stories_seen=stories_seen,
                pages_fetched=guard.pages_fetched,
                may_have_more=may_have_more,
            ),
        )
        return NewsResult(
            events=tuple(events),
            pages_fetched=guard.pages_fetched,
            stories_seen=stories_seen,
            may_have_more=may_have_more,
            endpoint_refs=tuple(endpoint_refs),
        )

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 400:
            raise BenzingaInvalidRequestError("benzinga invalid request")
        if status_code == 401:
            raise BenzingaAuthenticationFailedError("benzinga authentication failed")
        if status_code == 403:
            raise BenzingaEntitlementRequiredError("benzinga entitlement required")
        if status_code == 404:
            raise BenzingaNotFoundError("benzinga not found")
        raise BenzingaProviderError(f"benzinga provider error status={status_code}")
