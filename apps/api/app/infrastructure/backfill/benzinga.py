"""Benzinga bounded news BackfillSource (#309)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from app.core.backfill_settings import BackfillSettings
from app.infrastructure.benzinga.errors import (
    BenzingaAuthenticationFailedError,
    BenzingaEntitlementRequiredError,
    BenzingaProviderError,
)
from app.infrastructure.benzinga.news import BenzingaNewsConnector, NewsRequest
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


class BenzingaBackfillSource:
    """Wraps BenzingaNewsConnector. Does not own the connector."""

    def __init__(
        self,
        connector: BenzingaNewsConnector,
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
            raise BackfillSourceFetchError(detail="benzinga backfill source closed")
        if request.benzinga is None:
            raise BackfillSourceFetchError(detail="benzinga selector missing")
        selector = request.benzinga
        day = slice_.start_time.date().isoformat()
        # Prefer single-day bound for calendar-day slices; multi-day use date_from/date_to.
        end_day = (slice_.end_time.date()).isoformat()
        exclusive_midnight = (
            slice_.end_time.hour == 0
            and slice_.end_time.minute == 0
            and slice_.end_time.second == 0
            and slice_.end_time.microsecond == 0
        )
        if exclusive_midnight:
            end_day = (slice_.end_time.date() - timedelta(days=1)).isoformat()
        use_single = day == end_day
        try:
            result = await self._connector.fetch_news(
                NewsRequest(
                    date=day if use_single else None,
                    date_from=None if use_single else day,
                    date_to=None if use_single else end_day,
                    tickers=selector.tickers,
                    channels=selector.channels,
                    ticker_to_instrument=dict(selector.ticker_to_instrument),
                    anchor_instrument=selector.anchor_instrument,
                    sort="created:asc",
                    display_output="headline",
                )
            )
        except BenzingaEntitlementRequiredError as exc:
            raise BackfillEntitlementError(detail="benzinga entitlement required") from exc
        except BenzingaAuthenticationFailedError as exc:
            raise BackfillAuthError(detail="benzinga authentication failed") from exc
        except BenzingaProviderError as exc:
            text = str(exc).lower()
            if "429" in text:
                raise BackfillRateLimitError(detail="benzinga rate limited") from exc
            raise BackfillSourceFetchError(detail="benzinga fetch failed") from exc
        except Exception as exc:
            raise BackfillSourceFetchError(detail="benzinga fetch failed") from exc

        if result.may_have_more:
            raise BackfillTruncatedError(
                detail="benzinga may_have_more after page budget; shrink slice"
            )

        cursor = {
            "pages_fetched": str(result.pages_fetched),
            "slice_id": slice_.slice_id,
            "stories_seen": str(result.stories_seen),
        }
        return list(result.events), False, result.pages_fetched, cursor

    async def aclose(self) -> None:
        self._closed = True
