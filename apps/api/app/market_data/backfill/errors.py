"""Typed fail-closed Historical Backfill errors (#309)."""

from __future__ import annotations


class BackfillError(Exception):
    """Base typed backfill failure. Safe messages only — no payloads/secrets."""

    code: str = "backfill.error"

    def __init__(self, code: str | None = None, *, detail: str | None = None) -> None:
        self.code = code or self.code
        self.detail = detail
        message = self.code if detail is None else f"{self.code}: {detail}"
        super().__init__(message)


class BackfillDisabledError(BackfillError):
    code = "backfill.disabled"


class BackfillInvalidRequestError(BackfillError):
    code = "backfill.invalid_request"


class BackfillUnboundedRequestError(BackfillError):
    code = "backfill.unbounded_request"


class BackfillUnsupportedProviderError(BackfillError):
    code = "backfill.unsupported_provider"


class BackfillUnsupportedSourceError(BackfillError):
    code = "backfill.unsupported_source"


class BackfillSliceBuildError(BackfillError):
    code = "backfill.slice_build_failed"


class BackfillSourceFetchError(BackfillError):
    code = "backfill.source_fetch_failed"


class BackfillTruncatedError(BackfillError):
    """Connector reported may_have_more / hit page budget — fail closed."""

    code = "backfill.truncated"


class BackfillAuthError(BackfillError):
    code = "backfill.auth_failed"


class BackfillEntitlementError(BackfillError):
    code = "backfill.entitlement_required"


class BackfillRateLimitError(BackfillError):
    code = "backfill.rate_limited"


class BackfillMappingError(BackfillError):
    code = "backfill.mapping_failed"


class BackfillValidationError(BackfillError):
    code = "backfill.validation_failed"


class BackfillPitError(BackfillError):
    code = "backfill.pit_failed"


class BackfillSinkRequiredError(BackfillError):
    code = "backfill.sink_required"


class BackfillSinkFailedError(BackfillError):
    code = "backfill.sink_failed"


class BackfillCheckpointCorruptError(BackfillError):
    code = "backfill.checkpoint_corrupt"


class BackfillCheckpointMismatchError(BackfillError):
    code = "backfill.checkpoint_mismatch"


class BackfillCompletedError(BackfillError):
    code = "backfill.completed"


class BackfillCancelledError(BackfillError):
    code = "backfill.cancelled"


class BackfillBackpressureTimeoutError(BackfillError):
    code = "backfill.backpressure_timeout"


class BackfillClosedError(BackfillError):
    code = "backfill.closed"
