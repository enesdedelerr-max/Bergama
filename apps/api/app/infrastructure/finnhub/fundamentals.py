"""Finnhub basic financials → FundamentalEvent connector (Issue #304A)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.infrastructure.finnhub.errors import (
    FinnhubAuthenticationFailedError,
    FinnhubForbiddenError,
    FinnhubInvalidRequestError,
    FinnhubInvalidResponseError,
    FinnhubMappingFailedError,
    FinnhubNotConfiguredError,
    FinnhubNotFoundError,
    FinnhubProviderError,
)
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.mapper import map_fundamental_events
from app.infrastructure.finnhub.schemas import FinnhubBasicFinancials
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)


class FundamentalsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "symbol must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "currency must be a 3-letter ISO code when provided"
            raise ValueError(msg)
        return text


class FundamentalsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    events: tuple[FundamentalEvent, ...]
    symbol: str
    metric_count: int


class FinnhubFundamentalsConnector:
    """Fetch basic financials (metric=all) and map whitelist metrics."""

    def __init__(self, http: FinnhubHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_fundamentals(self, request: FundamentalsRequest) -> FundamentalsResult:
        if not self._http.settings.enabled:
            raise FinnhubNotConfiguredError("finnhub is disabled")

        observed_at = self._clock.now()
        response = await self._http.get(
            "/stock/metric",
            params={"symbol": request.symbol, "metric": "all"},
        )
        self._raise_for_status(response.status_code)
        request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-Id")

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise FinnhubInvalidResponseError("finnhub metrics response must be an object")
            parsed = FinnhubBasicFinancials.model_validate(payload)
        except FinnhubInvalidResponseError:
            raise
        except Exception as exc:
            raise FinnhubInvalidResponseError("invalid finnhub metrics response") from exc

        try:
            events = map_fundamental_events(
                parsed,
                instrument=request.instrument,
                symbol=request.symbol,
                observed_at=observed_at,
                request_id=request_id,
                caller_currency=request.currency,
            )
        except FinnhubMappingFailedError:
            raise
        except Exception as exc:
            raise FinnhubMappingFailedError("failed to map finnhub fundamentals") from exc

        logger.info(
            "finnhub fundamentals fetched",
            extra=structured_extra(
                event="finnhub.fundamentals.fetched",
                source="finnhub_fundamentals",
                symbol=request.symbol,
                event_count=len(events),
            ),
        )
        return FundamentalsResult(
            events=events,
            symbol=request.symbol,
            metric_count=len(events),
        )

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 400:
            raise FinnhubInvalidRequestError("finnhub invalid request")
        if status_code == 401:
            raise FinnhubAuthenticationFailedError("finnhub authentication failed")
        if status_code == 403:
            raise FinnhubForbiddenError("finnhub forbidden")
        if status_code == 404:
            raise FinnhubNotFoundError("finnhub not found")
        raise FinnhubProviderError(f"finnhub provider error status={status_code}")
