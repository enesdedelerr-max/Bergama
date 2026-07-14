"""Typed fail-closed Replay Engine errors (#308)."""

from __future__ import annotations


class ReplayError(Exception):
    """Base typed replay failure. Safe messages only — no payloads/secrets."""

    code: str = "replay.error"

    def __init__(self, code: str | None = None, *, detail: str | None = None) -> None:
        self.code = code or self.code
        self.detail = detail
        message = self.code if detail is None else f"{self.code}: {detail}"
        super().__init__(message)


class ReplayDisabledError(ReplayError):
    code = "replay.disabled"


class ReplayInvalidRequestError(ReplayError):
    code = "replay.invalid_request"


class ReplayUnboundedRequestError(ReplayError):
    code = "replay.unbounded_request"


class ReplaySourceReadError(ReplayError):
    code = "replay.source_read_failed"


class ReplayUnsupportedSchemaError(ReplayError):
    code = "replay.unsupported_schema"


class ReplayReconstructionError(ReplayError):
    code = "replay.reconstruction_failed"


class ReplayIdempotencyMismatchError(ReplayError):
    code = "replay.idempotency_mismatch"


class ReplayValidationError(ReplayError):
    code = "replay.validation_failed"


class ReplayPitError(ReplayError):
    code = "replay.pit_failed"


class ReplaySinkRequiredError(ReplayError):
    code = "replay.sink_required"


class ReplaySinkFailedError(ReplayError):
    code = "replay.sink_failed"


class ReplayCheckpointCorruptError(ReplayError):
    code = "replay.checkpoint_corrupt"


class ReplayCheckpointMismatchError(ReplayError):
    code = "replay.checkpoint_mismatch"


class ReplayCompletedError(ReplayError):
    code = "replay.completed"


class ReplayCancelledError(ReplayError):
    code = "replay.cancelled"


class ReplayBackpressureTimeoutError(ReplayError):
    code = "replay.backpressure_timeout"


class ReplayClosedError(ReplayError):
    code = "replay.closed"
