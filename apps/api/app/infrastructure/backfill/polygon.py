"""Polygon historical aggregates BackfillSource (#309)."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.backfill_settings import BackfillSettings
from app.infrastructure.polygon.errors import (
    PolygonAuthenticationFailedError,
    PolygonForbiddenError,
    PolygonPaginationLimitError,
    PolygonProviderError,
)
from app.infrastructure.polygon.historical import (
    HistoricalBarsRequest,
    PolygonHistoricalConnector,
    PolygonTimespan,
)
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


class PolygonHistoricalBackfillSource:
    """Wraps PolygonHistoricalConnector. Does not own the connector."""

    def __init__(
        self,
        connector: PolygonHistoricalConnector,
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
            raise BackfillSourceFetchError(detail="polygon backfill source closed")
        if request.polygon is None:
            raise BackfillSourceFetchError(detail="polygon selector missing")
        selector = request.polygon
        try:
            result = await self._connector.fetch_bars(
                HistoricalBarsRequest(
                    symbol=selector.ticker,
                    instrument=selector.instrument,
                    currency=selector.currency,
                    venue=selector.venue,
                    multiplier=selector.multiplier,
                    timespan=PolygonTimespan(selector.timespan),
                    start=slice_.start_time,
                    end=slice_.end_time,
                    adjusted=selector.adjusted,
                    sort="asc",
                )
            )
        except PolygonPaginationLimitError as exc:
            raise BackfillTruncatedError(detail="polygon page budget exceeded") from exc
        except PolygonAuthenticationFailedError as exc:
            raise BackfillAuthError(detail="polygon authentication failed") from exc
        except PolygonForbiddenError as exc:
            raise BackfillEntitlementError(detail="polygon forbidden") from exc
        except PolygonProviderError as exc:
            # Retry-After exhausted by connector — classify as rate-limit-ish terminal here.
            text = str(exc).lower()
            if "429" in text:
                raise BackfillRateLimitError(detail="polygon rate limited") from exc
            raise BackfillSourceFetchError(detail="polygon fetch failed") from exc
        except Exception as exc:
            raise BackfillSourceFetchError(detail="polygon fetch failed") from exc

        cursor = {
            "pages_fetched": str(result.pages_fetched),
            "slice_id": slice_.slice_id,
        }
        # Connector raises on page overrun; may_have_more is always false on success.
        return list(result.bars), False, result.pages_fetched, cursor

    async def aclose(self) -> None:
        self._closed = True
        # Connector is owned by AppContainer / caller when owns_connector=False.
