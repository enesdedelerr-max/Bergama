"""Typed Premarket Analyst Projection Core failures."""

from __future__ import annotations


class PremarketAnalystError(Exception):
    code = "premarket_analyst.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class PremarketAnalystValidationError(PremarketAnalystError):
    code = "premarket_analyst.validation_failed"


class PremarketAnalystUnauthorizedInputError(PremarketAnalystValidationError):
    code = "premarket_analyst.unauthorized_input"


class PremarketAnalystUnsupportedPolicyError(PremarketAnalystValidationError):
    code = "premarket_analyst.unsupported_policy"


class PremarketAnalystPitConflictError(PremarketAnalystValidationError):
    code = "premarket_analyst.pit_conflict"


class PremarketAnalystIdentityError(PremarketAnalystValidationError):
    code = "premarket_analyst.identity_violation"


class PremarketAnalystProvenanceError(PremarketAnalystValidationError):
    code = "premarket_analyst.provenance_violation"


class PremarketAnalystOrderingError(PremarketAnalystValidationError):
    code = "premarket_analyst.ordering_violation"


class PremarketAnalystDomainError(PremarketAnalystValidationError):
    code = "premarket_analyst.domain_violation"


class PremarketAnalystPipelineIsolationError(PremarketAnalystValidationError):
    code = "premarket_analyst.pipeline_isolation_violation"


class PremarketAnalystInvariantError(PremarketAnalystValidationError):
    code = "premarket_analyst.invariant_violation"


class PremarketAnalystReplayInequalityError(PremarketAnalystInvariantError):
    code = "premarket_analyst.replay_inequality"


class PremarketAnalystFailClosedError(PremarketAnalystValidationError):
    code = "premarket_analyst.fail_closed"
