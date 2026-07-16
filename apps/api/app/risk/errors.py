"""Typed Risk Engine failures."""

from __future__ import annotations


class RiskError(Exception):
    code = "risk.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class RiskConfigurationError(RiskError):
    code = "risk.configuration_invalid"


class RiskClosedError(RiskError):
    code = "risk.closed"


class RiskEvaluationError(RiskError):
    code = "risk.evaluation_failed"


class RiskDecimalError(RiskError):
    code = "risk.decimal_invalid"


class RiskDownstreamPortMissingError(RiskError):
    code = "risk.downstream_port_missing"


class RiskDownstreamPublishError(RiskError):
    code = "risk.downstream_publish_failed"
