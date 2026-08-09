"""Typed Dashboard Foundation failures."""

from __future__ import annotations


class DashboardError(Exception):
    code = "dashboard.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class DashboardValidationError(DashboardError):
    code = "dashboard.validation_failed"


class DashboardUnauthorizedInputError(DashboardValidationError):
    code = "dashboard.unauthorized_input"


class DashboardUnsupportedPolicyError(DashboardValidationError):
    code = "dashboard.unsupported_policy"


class DashboardPitConflictError(DashboardValidationError):
    code = "dashboard.pit_conflict"


class DashboardUpstreamPolicyError(DashboardValidationError):
    code = "dashboard.upstream_policy_mismatch"


class DashboardIdentityError(DashboardValidationError):
    code = "dashboard.identity_violation"


class DashboardProvenanceError(DashboardValidationError):
    code = "dashboard.provenance_violation"


class DashboardOrderingError(DashboardValidationError):
    code = "dashboard.ordering_violation"


class DashboardDomainError(DashboardValidationError):
    code = "dashboard.domain_violation"


class DashboardPipelineIsolationError(DashboardValidationError):
    code = "dashboard.pipeline_isolation_violation"


class DashboardConfigurationError(DashboardValidationError):
    code = "dashboard.configuration_stability_violation"


class DashboardOutputCompletenessError(DashboardValidationError):
    code = "dashboard.output_completeness_violation"


class DashboardInvariantError(DashboardValidationError):
    code = "dashboard.invariant_violation"


class DashboardReplayInequalityError(DashboardInvariantError):
    code = "dashboard.replay_inequality"
