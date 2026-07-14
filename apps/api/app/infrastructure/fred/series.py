"""FRED series metadata connector (Issue #304B)."""

from __future__ import annotations

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
from app.infrastructure.fred.mapper import SeriesMetadataView, map_series_metadata
from app.infrastructure.fred.schemas import FredSeriesResponse

logger = get_logger(__name__)


class SeriesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    series_id: str = Field(min_length=1, max_length=64)
    realtime_start: str | None = Field(default=None, min_length=10, max_length=10)
    realtime_end: str | None = Field(default=None, min_length=10, max_length=10)

    @field_validator("series_id")
    @classmethod
    def normalize_series_id(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "series_id must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("realtime_start", "realtime_end")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if len(text) != 10 or text[4] != "-" or text[7] != "-":
            msg = "realtime bounds must be YYYY-MM-DD"
            raise ValueError(msg)
        return text


class FredSeriesConnector:
    """Fetch /fred/series metadata (no Kafka / no MacroEvent emission)."""

    def __init__(self, http: FredHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_series(self, request: SeriesRequest) -> SeriesMetadataView:
        if not self._http.settings.enabled:
            raise FredNotConfiguredError("fred is disabled")

        _ = self._clock.now()  # injected clock reserved for future observation stamps
        params: dict[str, str] = {"series_id": request.series_id}
        if request.realtime_start is not None:
            params["realtime_start"] = request.realtime_start
        if request.realtime_end is not None:
            params["realtime_end"] = request.realtime_end

        response = await self._http.get("/fred/series", params=params)
        self._raise_for_status(response.status_code)

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise FredInvalidResponseError("fred series response must be an object")
            parsed = FredSeriesResponse.model_validate(payload)
        except FredInvalidResponseError:
            raise
        except Exception as exc:
            raise FredInvalidResponseError("invalid fred series response") from exc

        if not parsed.seriess:
            raise FredNotFoundError("fred series not found")

        try:
            meta = map_series_metadata(parsed.seriess[0])
        except FredMappingFailedError:
            raise
        except Exception as exc:
            raise FredMappingFailedError("failed to map fred series") from exc

        logger.info(
            "fred series fetched",
            extra=structured_extra(
                event="fred.series.fetched",
                source="fred_series",
                series_id=request.series_id,
            ),
        )
        return meta

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
