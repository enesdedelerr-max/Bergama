"""Finnhub bounded refresh BackfillSource (#309) — not historical series."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.backfill_settings import BackfillSettings
from app.infrastructure.finnhub.errors import (
    FinnhubAuthenticationFailedError,
    FinnhubForbiddenError,
    FinnhubProviderError,
)
from app.infrastructure.finnhub.fundamentals import (
    FinnhubFundamentalsConnector,
    FundamentalsRequest,
)
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector, ReferenceRequest
from app.market_data.backfill.errors import (
    BackfillAuthError,
    BackfillEntitlementError,
    BackfillRateLimitError,
    BackfillSourceFetchError,
)
from app.market_data.backfill.models import BackfillRequest, BackfillSlice
from app.market_data.backfill.slicing import build_slices
from app.market_data.envelope import CanonicalMarketEvent


class FinnhubRefreshSource:
    """Single-slice refresh of profile2 and/or basic metrics."""

    def __init__(
        self,
        *,
        reference: FinnhubReferenceConnector | None,
        fundamentals: FinnhubFundamentalsConnector | None,
        settings: BackfillSettings,
        owns_connector: bool = False,
    ) -> None:
        self._reference = reference
        self._fundamentals = fundamentals
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
            raise BackfillSourceFetchError(detail="finnhub refresh source closed")
        if request.finnhub is None:
            raise BackfillSourceFetchError(detail="finnhub selector missing")
        selector = request.finnhub
        events: list[CanonicalMarketEvent] = []
        request_count = 0
        try:
            if selector.refresh_type in {"profile", "both"}:
                if self._reference is None:
                    raise BackfillSourceFetchError(detail="finnhub reference connector unavailable")
                ref = await self._reference.fetch_reference(
                    ReferenceRequest(
                        symbol=selector.ticker,
                        instrument=selector.instrument,
                        currency=selector.currency,
                    )
                )
                events.append(ref)
                request_count += 1
            if selector.refresh_type in {"fundamentals", "both"}:
                if self._fundamentals is None:
                    raise BackfillSourceFetchError(
                        detail="finnhub fundamentals connector unavailable"
                    )
                result = await self._fundamentals.fetch_fundamentals(
                    FundamentalsRequest(
                        symbol=selector.ticker,
                        instrument=selector.instrument,
                        currency=selector.currency,
                    )
                )
                events.extend(result.events)
                request_count += 1
        except FinnhubAuthenticationFailedError as exc:
            raise BackfillAuthError(detail="finnhub authentication failed") from exc
        except FinnhubForbiddenError as exc:
            raise BackfillEntitlementError(detail="finnhub forbidden") from exc
        except FinnhubProviderError as exc:
            text = str(exc).lower()
            if "429" in text:
                raise BackfillRateLimitError(detail="finnhub rate limited") from exc
            raise BackfillSourceFetchError(detail="finnhub fetch failed") from exc
        except (BackfillAuthError, BackfillEntitlementError, BackfillRateLimitError):
            raise
        except Exception as exc:
            raise BackfillSourceFetchError(detail="finnhub fetch failed") from exc

        cursor = {"slice_id": "refresh-0", "request_count": str(request_count)}
        return events, False, request_count, cursor

    async def aclose(self) -> None:
        self._closed = True
