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


class GapError(PremarketError):
    code = "premarket.gap.error"


class GapValidationError(GapError):
    code = "premarket.gap.validation_failed"


class GapUnsupportedEventError(GapValidationError):
    code = "premarket.gap.unsupported_event"


class GapStaleKnownAtError(GapValidationError):
    code = "premarket.gap.stale_known_at"


class GapMissingBarError(GapValidationError):
    code = "premarket.gap.missing_bar"


class GapZeroCloseError(GapValidationError):
    code = "premarket.gap.zero_close"


class GapAmbiguousSelectionError(GapValidationError):
    code = "premarket.gap.ambiguous_selection"


class GapDuplicateInstrumentError(GapValidationError):
    code = "premarket.gap.duplicate_instrument"


class ScoreError(PremarketError):
    code = "premarket.score.error"


class ScoreValidationError(ScoreError):
    code = "premarket.score.validation_failed"


class ScoreUnsupportedPolicyError(ScoreValidationError):
    code = "premarket.score.unsupported_policy"


class ScoreDuplicateInstrumentError(ScoreValidationError):
    code = "premarket.score.duplicate_instrument"


class ScoreConflictError(ScoreValidationError):
    code = "premarket.score.conflict"


class ScoreDomainError(ScoreValidationError):
    code = "premarket.score.domain_violation"


class ScoreStaleKnownAtError(ScoreValidationError):
    code = "premarket.score.stale_known_at"


class ScoreInvariantError(ScoreValidationError):
    code = "premarket.score.invariant_violation"
