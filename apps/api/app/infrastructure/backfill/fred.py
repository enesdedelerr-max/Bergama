"""FRED observations BackfillSource (#309)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from app.core.backfill_settings import BackfillSettings
from app.infrastructure.fred.errors import (
    FredAuthenticationFailedError,
    FredForbiddenError,
    FredPaginationLimitError,
    FredProviderError,
)
from app.infrastructure.fred.observations import FredObservationsConnector, ObservationsRequest
from app.market_data.backfill.errors import (
    BackfillAuthError,
    BackfillEntitlementError,
    BackfillRateLimitError,
    BackfillSourceFetchError,
    BackfillTruncatedError,
)
from app.market_data.backfill.models import BackfillRequest, BackfillSlice
from app.market_data.backfill.slicing import build_slices
from app.market_data.envelope import CanonicalMarketEvent


class FredBackfillSource:
    """Wraps FredObservationsConnector. Does not own the connector."""

    def __init__(
        self,
        connector: FredObservationsConnector,
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
        if self._closed:
            raise BackfillSourceFetchError(detail="fred backfill source closed")
        if request.fred is None:
            raise BackfillSourceFetchError(detail="fred selector missing")
        selector = request.fred
        obs_start = slice_.start_time.date().isoformat()
        # Inclusive end day for FRED observation dates from exclusive slice end.
        exclusive_midnight = (
            slice_.end_time.hour == 0
            and slice_.end_time.minute == 0
            and slice_.end_time.second == 0
            and slice_.end_time.microsecond == 0
        )
        if exclusive_midnight:
            obs_end = (slice_.end_time.date() - timedelta(days=1)).isoformat()
        else:
            obs_end = slice_.end_time.date().isoformat()
        if obs_end < obs_start:
            return [], False, 0, {"slice_id": slice_.slice_id, "pages_fetched": "0"}

        try:
            result = await self._connector.fetch_observations(
                ObservationsRequest(
                    fred_series_id=selector.fred_series_id,
                    series_id=selector.series_id,
                    instrument=selector.instrument,
                    observation_start=obs_start,
                    observation_end=obs_end,
                    realtime_start=selector.realtime_start,
                    realtime_end=selector.realtime_end,
                    sort_order="asc",
                )
            )
        except FredPaginationLimitError as exc:
            raise BackfillTruncatedError(detail="fred page budget exceeded") from exc
        except FredAuthenticationFailedError as exc:
            raise BackfillAuthError(detail="fred authentication failed") from exc
        except FredForbiddenError as exc:
            raise BackfillEntitlementError(detail="fred forbidden") from exc
        except FredProviderError as exc:
            text = str(exc).lower()
            if "429" in text:
                raise BackfillRateLimitError(detail="fred rate limited") from exc
            raise BackfillSourceFetchError(detail="fred fetch failed") from exc
        except Exception as exc:
            raise BackfillSourceFetchError(detail="fred fetch failed") from exc

        cursor = {
            "pages_fetched": str(result.pages_fetched),
            "slice_id": slice_.slice_id,
            "skipped_missing": str(result.skipped_missing),
        }
        return list(result.events), False, result.pages_fetched, cursor

    async def aclose(self) -> None:
        self._closed = True
