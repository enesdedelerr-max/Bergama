"""SEC filings.recent refresh BackfillSource (#309) — not archive history."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.backfill_settings import BackfillSettings
from app.infrastructure.sec.errors import SecForbiddenError, SecNotFoundError, SecProviderError
from app.infrastructure.sec.submissions import SecSubmissionsConnector, SubmissionsRequest
from app.market_data.backfill.errors import (
    BackfillAuthError,
    BackfillEntitlementError,
    BackfillRateLimitError,
    BackfillSourceFetchError,
)
from app.market_data.backfill.models import BackfillRequest, BackfillSlice
from app.market_data.backfill.slicing import build_slices
from app.market_data.envelope import CanonicalMarketEvent


class SecRefreshSource:
    """Single-slice SEC submissions.recent refresh. Sequential only."""

    def __init__(
        self,
        connector: SecSubmissionsConnector,
        settings: BackfillSettings,
        *,
        owns_connector: bool = False,
    ) -> None:
        self._connector = connector
        self._settings = settings
        self._owns_connector = owns_connector
        self._closed = False

    def build_slices(self, request: BackfillRequest) -> Sequence[BackfillSlice]:
        return build_slices(request, self._settings)

    async def fetch_slice(
        self,
        slice_: BackfillSlice,
        request: BackfillRequest,
    ) -> tuple[Sequence[CanonicalMarketEvent], bool, int, dict[str, str]]:
        _ = slice_
        if self._closed:
            raise BackfillSourceFetchError(detail="sec refresh source closed")
        if request.sec is None:
            raise BackfillSourceFetchError(detail="sec selector missing")
        selector = request.sec
        try:
            result = await self._connector.fetch_submissions(
                SubmissionsRequest(
                    cik=selector.cik,
                    instrument=selector.instrument,
                    max_filings=selector.max_filings,
                )
            )
        except SecForbiddenError as exc:
            raise BackfillEntitlementError(detail="sec forbidden") from exc
        except SecNotFoundError as exc:
            raise BackfillSourceFetchError(detail="sec not found") from exc
        except SecProviderError as exc:
            text = str(exc).lower()
            if "429" in text:
                raise BackfillRateLimitError(detail="sec rate limited") from exc
            if "401" in text or "auth" in text:
                raise BackfillAuthError(detail="sec authentication failed") from exc
            raise BackfillSourceFetchError(detail="sec fetch failed") from exc
        except Exception as exc:
            raise BackfillSourceFetchError(detail="sec fetch failed") from exc

        cursor = {
            "slice_id": "refresh-0",
            "filings_mapped": str(result.filings_mapped),
            "cik": result.cik,
        }
        return list(result.events), False, 1, cursor

    async def aclose(self) -> None:
        self._closed = True
