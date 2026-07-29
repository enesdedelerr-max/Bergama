"""Typed Premarket Intelligence failures."""

from __future__ import annotations


class PremarketError(Exception):
    code = "premarket.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class PremarketDisabledError(PremarketError):
    code = "premarket.disabled"


class WatchlistError(PremarketError):
    code = "premarket.watchlist.error"


class WatchlistValidationError(WatchlistError):
    code = "premarket.watchlist.validation_failed"


class WatchlistDuplicateInstrumentError(WatchlistValidationError):
    code = "premarket.watchlist.duplicate_instrument"


class WatchlistUnsupportedCandidateError(WatchlistValidationError):
    code = "premarket.watchlist.unsupported_candidate"


class CatalystError(PremarketError):
    code = "premarket.catalyst.error"


class CatalystValidationError(CatalystError):
    code = "premarket.catalyst.validation_failed"


class CatalystUnsupportedEventError(CatalystValidationError):
    code = "premarket.catalyst.unsupported_event"


class CatalystIdentityConflictError(CatalystValidationError):
    code = "premarket.catalyst.identity_conflict"


class CatalystStaleKnownAtError(CatalystValidationError):
    code = "premarket.catalyst.stale_known_at"


class CatalystClassificationError(CatalystValidationError):
    code = "premarket.catalyst.classification_failed"
