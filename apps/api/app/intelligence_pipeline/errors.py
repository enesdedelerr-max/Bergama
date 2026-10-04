"""Thin Intelligence Pipeline composition failures."""

from __future__ import annotations


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
