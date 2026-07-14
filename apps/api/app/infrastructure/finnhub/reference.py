"""Finnhub company profile → ReferenceDataEvent connector (Issue #304A)."""

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
from app.infrastructure.finnhub.mapper import map_reference_event
from app.infrastructure.finnhub.schemas import FinnhubCompanyProfile2
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)


class ReferenceRequest(BaseModel):
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


class FinnhubReferenceConnector:
    """Fetch Company Profile 2 and map to canonical ReferenceDataEvent."""

    def __init__(self, http: FinnhubHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_reference(self, request: ReferenceRequest) -> ReferenceDataEvent:
        if not self._http.settings.enabled:
            raise FinnhubNotConfiguredError("finnhub is disabled")

        observed_at = self._clock.now()
        response = await self._http.get("/stock/profile2", params={"symbol": request.symbol})
        self._raise_for_status(response.status_code)
        request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-Id")

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise FinnhubInvalidResponseError("finnhub profile response must be an object")
            profile = FinnhubCompanyProfile2.model_validate(payload)
        except FinnhubInvalidResponseError:
            raise
        except Exception as exc:
            raise FinnhubInvalidResponseError("invalid finnhub profile response") from exc

        if profile.is_empty():
            raise FinnhubNotFoundError("finnhub company profile not found")

        try:
            event = map_reference_event(
                profile,
                instrument=request.instrument,
                symbol=request.symbol,
                observed_at=observed_at,
                request_id=request_id,
                caller_currency=request.currency,
            )
        except FinnhubMappingFailedError:
            raise
        except Exception as exc:
            raise FinnhubMappingFailedError("failed to map finnhub profile") from exc

        logger.info(
            "finnhub reference fetched",
            extra=structured_extra(
                event="finnhub.reference.fetched",
                source="finnhub_reference",
                symbol=request.symbol,
            ),
        )
        return event

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
