"""Typed configuration and runtime errors for the market-data orchestrator (#305)."""

from __future__ import annotations


class OrchestratorError(Exception):
    """Base orchestrator failure."""

    code: str = "orchestrator.error"

    def __init__(self, code: str | None = None, *, detail: str | None = None) -> None:
        self.code = code or self.code
        self.detail = detail
        message = self.code if detail is None else f"{self.code}: {detail}"
        super().__init__(message)


class OrchestratorConfigurationError(OrchestratorError):
    """Fail-closed configuration error (missing PublishPort, invalid wiring)."""

    code = "orchestrator.configuration_error"


class OrchestratorClosedError(OrchestratorError):
    """Raised when process is called after aclose()."""

    code = "orchestrator.closed"
