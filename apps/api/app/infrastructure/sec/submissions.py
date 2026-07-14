"""SEC EDGAR company submissions → FilingEvent connector (Issue #304C)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.infrastructure.sec.accession import normalize_cik
from app.infrastructure.sec.errors import (
    SecForbiddenError,
    SecInvalidRequestError,
    SecInvalidResponseError,
    SecMappingFailedError,
    SecNotConfiguredError,
    SecNotFoundError,
    SecProviderError,
)
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.mapper import archive_file_refs, map_recent_filings
from app.infrastructure.sec.schemas import SecSubmissionsResponse
from app.market_data.events.filing import FilingEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)


class SubmissionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cik: str = Field(min_length=1, max_length=16)
    instrument: InstrumentId
    max_filings: int | None = Field(default=None, ge=1, le=1000)

    @field_validator("cik")
    @classmethod
    def normalize_cik_field(cls, value: str) -> str:
        return normalize_cik(value)


class SubmissionsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    events: tuple[FilingEvent, ...]
    cik: str
    entity_name: str | None
    archive_files: tuple[dict[str, str], ...]
    filings_mapped: int


class SecSubmissionsConnector:
    """Fetch company submissions and map filings.recent only."""

    def __init__(self, http: SecHttpClient, *, clock: Clock) -> None:
        self._http = http
        self._clock = clock

    async def fetch_submissions(self, request: SubmissionsRequest) -> SubmissionsResult:
        if not self._http.settings.enabled:
            raise SecNotConfiguredError("sec is disabled")

        cik10 = request.cik
        ingested_at = self._clock.now()
        path = f"/submissions/CIK{cik10}.json"
        response = await self._http.get(path)
        self._raise_for_status(response.status_code)

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise SecInvalidResponseError("sec submissions response must be an object")
            parsed = SecSubmissionsResponse.model_validate(payload)
        except SecInvalidResponseError:
            raise
        except Exception as exc:
            raise SecInvalidResponseError("invalid sec submissions response") from exc

        max_filings = (
            request.max_filings
            if request.max_filings is not None
            else self._http.settings.max_filings_per_request
        )

        try:
            events = map_recent_filings(
                parsed,
                instrument=request.instrument,
                cik10=cik10,
                archives_base_url=self._http.settings.archives_base_url,
                ingested_at=ingested_at,
                max_filings=max_filings,
            )
            archives = archive_file_refs(parsed)
        except SecMappingFailedError:
            raise
        except SecInvalidResponseError:
            raise
        except Exception as exc:
            raise SecMappingFailedError("failed to map sec submissions") from exc

        logger.info(
            "sec submissions fetched",
            extra=structured_extra(
                event="sec.submissions.fetched",
                source="sec_submissions",
                cik=cik10,
                event_count=len(events),
                archive_file_count=len(archives),
            ),
        )
        return SubmissionsResult(
            events=events,
            cik=cik10,
            entity_name=parsed.name.strip()[:256] if parsed.name else None,
            archive_files=archives,
            filings_mapped=len(events),
        )

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 400:
            raise SecInvalidRequestError("sec invalid request")
        if status_code == 403:
            raise SecForbiddenError("sec forbidden")
        if status_code == 404:
            raise SecNotFoundError("sec not found")
        raise SecProviderError(f"sec provider error status={status_code}")
