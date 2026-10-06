"""Thin Intelligence Pipeline composition failures."""

from __future__ import annotations

from app.intelligence_pipeline.policy import FAILURE_DETAIL_MAX_LENGTH


class PipelineError(Exception):
    """Base composition error. Stage business reasons remain stage-owned."""

    code = "intelligence_pipeline.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class PipelineAdmissionError(PipelineError):
    """Fail-closed admission rejection before governed stage execution."""

    code = "intelligence_pipeline.admission_rejected"


class PipelineStageExecutionError(PipelineError):
    """Composition wrapper for a required stage failure."""

    code = "intelligence_pipeline.required_stage_failed"

    def __init__(
        self,
        message: str | None = None,
        *,
        detail: str | None = None,
        stage: str | None = None,
        upstream_error_type: str | None = None,
    ) -> None:
        super().__init__(message, detail=detail)
        self.stage = stage
        self.upstream_error_type = upstream_error_type


class PipelineReplayInequalityError(PipelineError):
    """Fail-closed replay equality mismatch (not a PipelineOutcome)."""

    code = "intelligence_pipeline.replay_inequality"

    def __init__(
        self,
        message: str | None = None,
        *,
        detail: str | None = None,
        mismatches: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message, detail=detail)
        self.mismatches = mismatches


def sanitize_failure_detail(detail: str | None) -> str | None:
    """Bound public failure detail for deterministic, fail-closed surfaces."""
    if detail is None:
        return None
    cleaned = "".join(ch for ch in detail if ch in "\t\n" or ord(ch) >= 32)
    if not cleaned:
        return None
    if len(cleaned) > FAILURE_DETAIL_MAX_LENGTH:
        return cleaned[:FAILURE_DETAIL_MAX_LENGTH]
    return cleaned
