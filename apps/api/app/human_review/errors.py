"""Typed Human Review Foundation failures."""

from __future__ import annotations


class HumanReviewError(Exception):
    code = "human_review.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class HumanReviewValidationError(HumanReviewError):
    code = "human_review.validation_failed"


class HumanReviewUnauthorizedInputError(HumanReviewValidationError):
    code = "human_review.unauthorized_input"


class HumanReviewUnsupportedPolicyError(HumanReviewValidationError):
    code = "human_review.unsupported_policy"


class HumanReviewPitConflictError(HumanReviewValidationError):
    code = "human_review.pit_conflict"


class HumanReviewUpstreamPolicyError(HumanReviewValidationError):
    code = "human_review.upstream_policy_mismatch"


class HumanReviewHumanAuthorityError(HumanReviewValidationError):
    code = "human_review.human_authority_violation"


class HumanReviewIdentityError(HumanReviewValidationError):
    code = "human_review.identity_violation"


class HumanReviewProvenanceError(HumanReviewValidationError):
    code = "human_review.provenance_violation"


class HumanReviewHistoryError(HumanReviewValidationError):
    code = "human_review.history_violation"


class HumanReviewOrderingError(HumanReviewValidationError):
    code = "human_review.ordering_violation"


class HumanReviewDomainError(HumanReviewValidationError):
    code = "human_review.domain_violation"


class HumanReviewPipelineIsolationError(HumanReviewValidationError):
    code = "human_review.pipeline_isolation_violation"


class HumanReviewConfigurationError(HumanReviewValidationError):
    code = "human_review.configuration_stability_violation"


class HumanReviewOutputCompletenessError(HumanReviewValidationError):
    code = "human_review.output_completeness_violation"


class HumanReviewInvariantError(HumanReviewValidationError):
    code = "human_review.invariant_violation"


class HumanReviewReplayInequalityError(HumanReviewInvariantError):
    code = "human_review.replay_inequality"
