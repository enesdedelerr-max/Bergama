"""Typed Strategy Engine failures."""

from __future__ import annotations


class StrategyError(Exception):
    code = "strategy.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class StrategyConfigurationError(StrategyError):
    code = "strategy.configuration_invalid"


class StrategyUnsupportedEventError(StrategyError):
    code = "strategy.unsupported_event"


class StrategyPitViolationError(StrategyError):
    code = "strategy.pit_violation"


class StrategyQualityRejectedError(StrategyError):
    code = "strategy.quality_rejected"


class StrategyDuplicateInputError(StrategyError):
    code = "strategy.duplicate_input"


class StrategyStateConflictError(StrategyError):
    code = "strategy.state_conflict"


class StrategyEvaluationError(StrategyError):
    code = "strategy.evaluation_failed"


class StrategyOutputValidationError(StrategyError):
    code = "strategy.output_invalid"


class StrategyClosedError(StrategyError):
    code = "strategy.closed"


class StrategyDownstreamPortMissingError(StrategyError):
    code = "strategy.downstream_port_missing"


class StrategyDownstreamPublishError(StrategyError):
    code = "strategy.downstream_publish_failed"


class StrategyRegistryError(StrategyError):
    code = "strategy.registry_error"


class StrategyAlreadyRegisteredError(StrategyRegistryError):
    code = "strategy.already_registered"


class StrategyNotFoundError(StrategyRegistryError):
    code = "strategy.not_found"
